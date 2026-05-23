from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Trip
from .serializers import TripSerializer
from network.utils import shortest_path
from network.models import Node
# from carpools.models import RideRequest
# from carpools.serializers import RideRequestSerializer
# from carpools.utils import is_request_matching_trip, calculate_detour_and_fare

# Create your tests here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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

    def get(self, request):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can view their trips."},
                status=status.HTTP_403_FORBIDDEN
            )

        trips = Trip.objects.filter(driver=request.user).order_by('-created_at')
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can publish trips."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TripSerializer(data=request.data)

        if serializer.is_valid():
            start_id       = serializer.validated_data['start_node'].id
            end_id         = serializer.validated_data['end_node'].id
            max_passengers = serializer.validated_data['max_passengers']

            distance, path = shortest_path(start_id, end_id)

            if not path:
                return Response(
                    {"error": "No valid route found between these nodes."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            trip = serializer.save(
                driver=request.user,
                route=path,
                available_seats=max_passengers,
                visited_nodes=[path[0]],
                current_node_id=Node.objects.get(path[0])
            )

            return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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
        trip.current_node_id = node_id

        if node_id == trip.end_node_id:
            trip.status = 'COMPLETED'
            message = "Destination reached! Trip is now complete."
        else:
            message = "Location updated successfully."

        trip.save()

        return Response({
            "message":       message,
            "current_node":  node_id,
            "visited_nodes": new_visited
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# DRIVER SEES INCOMING CARPOOL REQUESTS
# GET /api/trips/<id>/requests/  → matching requests for this trip
# ─────────────────────────────────────────────
class DriverRequestsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can view carpool requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        trip = get_object_or_404(Trip, id=trip_id, driver=request.user)

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