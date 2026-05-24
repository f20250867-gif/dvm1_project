from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from network.models import Node,ServiceStatus
from trips.models import Trip
from .models import RideRequest, RideOffer
from .utils import calculate_detour_and_fare
from users.models import Transaction
from decimal import Decimal

# Create your views here.


@login_required
def passenger_dashboard(request):
    if request.user.role != 'PASSENGER':
        return redirect('driver_dashboard')

    if request.method == 'POST':
        service, _ = ServiceStatus.objects.get_or_create(
            id=1,
            defaults={'is_active': True}
        )
        if not service.is_active:
            messages.error(request, 'Carpooling service is currently suspended.')
            return redirect('passenger_dashboard')

        pickup_id = request.POST.get('pickup_node')
        drop_id   = request.POST.get('drop_node')

        if pickup_id == drop_id:
            messages.error(request, 'Pickup and drop cannot be the same.')
        else:
            # check matching trips exist including active ones
            from .utils import find_matching_trips
            matches = find_matching_trips(int(pickup_id), int(drop_id))

            if not matches:
                messages.warning(request, 'No matching trips found right now. Request submitted anyway!')
            else:
                messages.success(request, f'{len(matches)} matching trip(s) found!')

            RideRequest.objects.create(
                passenger      = request.user,
                pickup_node_id = pickup_id,
                drop_node_id   = drop_id,
            )
            return redirect('passenger_dashboard')

    nodes         = Node.objects.all()
    ride_requests = RideRequest.objects.filter(
        passenger=request.user
    ).order_by('-created_at')

    return render(request, 'carpools/passenger_dashboard.html', {
        'nodes':         nodes,
        'ride_requests': ride_requests
    })

class MakeOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can make offers."},
                status=status.HTTP_403_FORBIDDEN
            )

        trip_id         = request.data.get("trip_id")
        ride_request_id = request.data.get("ride_request_id")

        # safe get with error handling
        try:
            trip         = Trip.objects.get(id=trip_id, driver=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            ride_request = RideRequest.objects.get(id=ride_request_id, status='pending')
        except RideRequest.DoesNotExist:
            return Response({"error": "Ride request not found or not pending."}, status=status.HTTP_404_NOT_FOUND)

        # check duplicate offer
        if RideOffer.objects.filter(trip=trip, ride_request=ride_request).exists():
            return Response(
                {"error": "You have already made an offer for this request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # check seats
        if trip.available_seats <= 0:
            return Response(
                {"error": "Your trip is already full."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # check trip is active or scheduled
        if trip.status not in ['SCHEDULED', 'ACTIVE']:
            return Response(
                {"error": "Can only make offers on active or scheduled trips."},
                status=status.HTTP_400_BAD_REQUEST
            )

        detour, fare = calculate_detour_and_fare(trip, ride_request)

        if detour == float('inf'):
            return Response(
                {"error": "No valid route found to serve this passenger."},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer = RideOffer.objects.create(
            trip          = trip,
            ride_request  = ride_request,
            detour        = detour,       # ← save detour
            proposed_fare = fare,
            status        = 'pending'
        )

        return Response({
            "message": "Offer created successfully.",
            "offer_id": offer.id,
            "detour":   detour,
            "fare":     fare
        }, status=status.HTTP_201_CREATED)

class AcceptOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, offer_id):
        if request.user.role != 'PASSENGER':
            return Response(
                {"error": "Only passengers can accept offers."},
                status=status.HTTP_403_FORBIDDEN
            )

        offer = get_object_or_404(
            RideOffer,
            id=offer_id,
            ride_request__passenger=request.user
        )

        if offer.status != 'pending':
            return Response(
                {"error": f"This offer is already {offer.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        trip = offer.trip

        if trip.available_seats <= 0:
            return Response(
                {"error": "Sorry, this trip is already full."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # atomic — all or nothing
        with transaction.atomic():
            offer.status = 'accepted'
            offer.save()

            ride_request        = offer.ride_request
            ride_request.status = 'matched'
            ride_request.save()

            trip.available_seats -= 1
            trip.save()

            # reject all other pending offers for same request
            RideOffer.objects.filter(
                ride_request=ride_request,
                status='pending'
            ).exclude(id=offer.id).update(status='rejected')

        return Response({
            "message": "Offer accepted! Your ride is confirmed.",
            "trip_id": trip.id,
            "fare":    offer.proposed_fare
        }, status=status.HTTP_200_OK)

class ViewOffersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):
        if request.user.role != 'PASSENGER':
            return Response(
                {"error": "Only passengers can view offers."},
                status=status.HTTP_403_FORBIDDEN
            )

        # make sure request belongs to this passenger
        ride_request = get_object_or_404(
            RideRequest,
            id=request_id,
            passenger=request.user
        )

        if ride_request.status == 'cancelled':
            return Response(
                {"error": "This request has been cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        offers = RideOffer.objects.filter(
            ride_request=ride_request
        ).select_related('trip__driver')   # ← avoids N+1 queries

        if not offers.exists():
            return Response(
                {"message": "No offers yet. Check back later."},
                status=status.HTTP_200_OK
            )

        data = []
        for offer in offers:
            data.append({
                "offer_id":    offer.id,
                "driver":      offer.trip.driver.username,
                "trip_id":     offer.trip.id,
                "detour":      offer.detour,
                "fare":        offer.proposed_fare,
                "status":      offer.status,
            })

        return Response(data, status=status.HTTP_200_OK)


class CancelRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, request_id):
        if request.user.role != 'PASSENGER':
            return Response(
                {"error": "Only passengers can cancel requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        ride_request = get_object_or_404(
            RideRequest,
            id=request_id,
            passenger=request.user
        )

        # can only cancel if not already matched or completed
        if ride_request.status == 'matched':
            return Response(
                {"error": "Cannot cancel a request that has already been matched."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if ride_request.status == 'completed':
            return Response(
                {"error": "Cannot cancel a completed request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if ride_request.status == 'cancelled':
            return Response(
                {"error": "Request is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # reject all pending offers for this request
            RideOffer.objects.filter(
                ride_request=ride_request,
                status='pending'
            ).update(status='rejected')

            ride_request.status = 'cancelled'
            ride_request.save()

        return Response(
            {"message": "Request cancelled successfully."},
            status=status.HTTP_200_OK
        )

@login_required
def view_offers_page(request, request_id):
    if request.user.role != 'PASSENGER':
        return redirect('driver_dashboard')

    ride_request = get_object_or_404(RideRequest, id=request_id, passenger=request.user)
    offers       = RideOffer.objects.filter(ride_request=ride_request).select_related('trip__driver')

    return render(request, 'carpools/view_offers.html', {
        'ride_request': ride_request,
        'offers':       offers
    })


@login_required
def confirm_offer_page(request, offer_id):
    if request.user.role != 'PASSENGER':
        return redirect('driver_dashboard')

    offer = get_object_or_404(RideOffer, id=offer_id, ride_request__passenger=request.user)

    if offer.status != 'pending':
        messages.error(request, f'This offer is already {offer.status}.')
        return redirect('passenger_dashboard')

    trip = offer.trip
    if trip.available_seats <= 0:
        messages.error(request, 'Sorry this trip is already full.')
        return redirect('passenger_dashboard')

    with transaction.atomic():
        offer.status = 'accepted'
        offer.save()

        ride_request        = offer.ride_request
        ride_request.status = 'matched'
        ride_request.save()

        trip.available_seats -= 1
        trip.save()

        RideOffer.objects.filter(
            ride_request=ride_request,
            status='pending'
        ).exclude(id=offer.id).update(status='rejected')

    messages.success(request, 'Ride confirmed!')
    return redirect('passenger_dashboard')


@login_required
def cancel_request_page(request, request_id):
    if request.user.role != 'PASSENGER':
        return redirect('driver_dashboard')

    ride_request = get_object_or_404(RideRequest, id=request_id, passenger=request.user)

    if ride_request.status in ['matched', 'completed', 'cancelled']:
        messages.error(request, f'Cannot cancel a {ride_request.status} request.')
        return redirect('passenger_dashboard')

    with transaction.atomic():
        RideOffer.objects.filter(
            ride_request=ride_request,
            status='pending'
        ).update(status='rejected')

        ride_request.status = 'cancelled'
        ride_request.save()

    messages.success(request, 'Request cancelled.')
    return redirect('passenger_dashboard')


@login_required
def make_offer_page(request, request_id):
    if request.user.role != 'DRIVER':
        return redirect('passenger_dashboard')

    trip_id      = request.POST.get('trip_id')
    trip         = get_object_or_404(Trip, id=trip_id, driver=request.user)
    ride_request = get_object_or_404(RideRequest, id=request_id, status='pending')

    if RideOffer.objects.filter(trip=trip, ride_request=ride_request).exists():
        messages.error(request, 'You already made an offer for this request.')
        return redirect('driver-dashboard-ssr', trip_id=trip.id)

    detour, fare = calculate_detour_and_fare(trip, ride_request)

    RideOffer.objects.create(
        trip          = trip,
        ride_request  = ride_request,
        detour        = detour,
        proposed_fare = fare,
        status        = 'pending'
    )

    messages.success(request, 'Offer made successfully!')
    return redirect('driver-dashboard-ssr', trip_id=trip.id)

@login_required
def wallet_topup_page(request):
    if request.user.role != 'PASSENGER':
        return redirect('driver_dashboard')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = Decimal(str(amount))   # ← changed from float to Decimal
            if amount <= 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, 'Please enter a valid amount.')
            return redirect('wallet-topup-page')

        with transaction.atomic():
            request.user.wallet_balance += amount
            request.user.save()
            Transaction.objects.create(
                user             = request.user,
                amount           = amount,
                transaction_type = 'topup',
                trip             = None
            )

        messages.success(request, f'₹{amount} added to your wallet!')
        return redirect('passenger_dashboard')

    return render(request, 'carpools/wallet_topup.html')

@login_required
def transaction_history(request):
    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'carpools/transaction_history.html', {
        'transactions': transactions
    })