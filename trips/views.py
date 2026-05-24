from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Trip
from .serializers import TripSerializer
from network.utils import shortest_path
from network.models import Node
from django.contrib import messages
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from users.models import Transaction


from carpools.models import RideRequest,RideOffer
from carpools.serializers import RideRequestSerializer
from carpools.utils import is_request_matching_trip, calculate_detour_and_fare

# Create your tests here.

@login_required
def driver_dashboard(request):
    nodes = Node.objects.all()
    trips = Trip.objects.filter(driver=request.user).order_by('-created_at')
    return render(request, 'trips/driver_dashboard.html', {
        'nodes': nodes,
        'trips': trips
    })

class TripView(APIView):
    permission_classes = [IsAuthenticated]

@login_required
def driver_dashboard(request):

    # handle form submission
    if request.method == 'POST':
        start_id       = request.POST.get('start_node')
        end_id         = request.POST.get('end_node')
        max_passengers = request.POST.get('max_passengers')

        # validation
        if start_id == end_id:
            messages.error(request, 'Start and end node cannot be the same.')
        else:
            distance, path = shortest_path(int(start_id), int(end_id))

            if not path:
                messages.error(request, 'No valid route found between these nodes.')
            else:
                Trip.objects.create(
                    driver          = request.user,
                    start_node_id   = start_id,
                    end_node_id     = end_id,
                    max_passengers  = max_passengers,
                    available_seats = max_passengers,
                    route           = path,
                    visited_nodes   = [path[0]],
                    current_node_id = path[0],
                    status          = 'SCHEDULED'
                )
                messages.success(request, 'Trip published successfully!')
                return redirect('driver_dashboard')

    # GET — show dashboard
    nodes = Node.objects.all()
    trips = Trip.objects.filter(driver=request.user).order_by('-created_at')

    return render(request, 'trips/driver_dashboard.html', {
        'nodes': nodes,
        'trips': trips
    })
    

class TripDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Trip.objects.get(pk=pk, driver=user)
        except Trip.DoesNotExist:
            return None

    def get(self, request, pk):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can view trip details."},
                status=status.HTTP_403_FORBIDDEN
            )

        trip = self.get_object(pk, request.user)
        if not trip:
            return Response(
                {"error": "Trip not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TripSerializer(trip)
        return Response(serializer.data)


class CancelTripView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, trip_id):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can cancel trips."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            trip = Trip.objects.get(id=trip_id, driver=request.user)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if len(trip.visited_nodes) > 1 or trip.current_node_id != trip.start_node_id:
            return Response(
                {"error": "Cannot cancel a trip that has already started."},
                status=status.HTTP_400_BAD_REQUEST
            )

        trip.status = 'CANCELLED'
        trip.save()
        return Response(
            {"message": "Trip cancelled successfully."},
            status=status.HTTP_200_OK
        )

class UpdateLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can update location."},
                status=status.HTTP_403_FORBIDDEN
            )

        trip_id = request.data.get("trip_id")

        try:
            node_id = int(request.data.get("node_id"))
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid node_id format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            trip = Trip.objects.get(id=trip_id, driver=request.user)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if trip.status == 'CANCELLED':
            return Response(
                {"error": "Cannot update a cancelled trip."},
                status=status.HTTP_400_BAD_REQUEST
            )

        route   = trip.route or []
        visited = trip.visited_nodes or []

        if node_id not in route:
            return Response(
                {"error": "This node is not on your planned route."},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_index = route.index(visited[-1]) if visited else -1
        new_index  = route.index(node_id)

        if new_index <= last_index:
            return Response(
                {"error": "Cannot revisit a previous node or go backwards."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_visited          = route[:new_index + 1]
        trip.visited_nodes   = new_visited
        trip.current_node    = Node.objects.get(id=node_id)

        # ← set ACTIVE on first move
        if trip.status == 'SCHEDULED':
            trip.status = 'ACTIVE'

        # ← set COMPLETED when end node reached
        if node_id == trip.end_node_id:
            trip.status = 'COMPLETED'
            message = "Destination reached! Trip is now complete."
        else:
            message = "Location updated successfully."

        trip.save()

        return Response({
            "message":       message,
            "current_node":  node_id,
            "visited_nodes": new_visited,
            "status":        trip.status   
        }, status=status.HTTP_200_OK)


class DriverRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can view carpool requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        trip = get_object_or_404(Trip, id=trip_id, driver=request.user,status__in=['SCHEDULED', 'ACTIVE'])

        pending_requests = RideRequest.objects.filter(
            status="pending"
        ).select_related('passenger')

        valid_requests_data = []
        for req in pending_requests:
            if is_request_matching_trip(trip, req.pickup_node_id, req.drop_node_id):
                detour, fare                 = calculate_detour_and_fare(trip, req)
                req_data                     = RideRequestSerializer(req).data
                req_data['detour_nodes']     = detour
                req_data['calculated_fare']  = fare
                valid_requests_data.append(req_data)

        return Response(valid_requests_data)


@login_required
def driver_dashboard_ssr(request, trip_id):
    if request.user.role != 'DRIVER':
        return redirect('passenger_dashboard')

    trip = get_object_or_404(Trip, id=trip_id, driver=request.user,status__in=['SCHEDULED', 'ACTIVE'])

    # get pending requests that driver hasn't offered on yet
    already_offered_request_ids = RideOffer.objects.filter(
        trip=trip
    ).values_list('ride_request_id', flat=True)

    base_requests = RideRequest.objects.filter(
        status='pending'
    ).exclude(
        id__in=already_offered_request_ids   # ← correct way
    )

    incoming_requests = []
    for req in base_requests:
        if is_request_matching_trip(trip, req.pickup_node.id, req.drop_node.id):
            detour, fare = calculate_detour_and_fare(trip, req)
            req.detour   = detour
            req.fare     = fare
            incoming_requests.append(req)

    pending_offers    = RideOffer.objects.filter(trip=trip, status='pending')
    confirmed_carpools = RideOffer.objects.filter(trip=trip, status='accepted')
    past_offers       = RideOffer.objects.filter(trip=trip, status='rejected')

    context = {
        'trip':               trip,
        'incoming_requests':  incoming_requests,
        'pending_offers':     pending_offers,
        'confirmed_carpools': confirmed_carpools,
        'past_offers':        past_offers,
    }
    return render(request, 'trips/driver_dashboard_ssr.html', context)  

@login_required
def cancel_trip_page(request, trip_id):
    if request.user.role != 'DRIVER':
        return redirect('passenger_dashboard')

    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)

    if trip.status != 'SCHEDULED':
        messages.error(request, 'Only scheduled trips can be cancelled.')
        return redirect('driver_dashboard')

    trip.status = 'CANCELLED'
    trip.save()

    messages.success(request, 'Trip cancelled successfully.')
    return redirect('driver_dashboard')

@login_required
def driver_transaction_history(request):
    from users.models import Transaction
    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'trips/driver_transaction_history.html', {
        'transactions': transactions
    })