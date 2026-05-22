from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Trip
from .serializers import TripSerializer
from network.utils import shortest_path
# from carpools.models import RideRequest
# from carpools.serializers import RideRequestSerializer
# from carpools.utils import is_request_matching_trip, calculate_detour_and_fare

# Create your tests here.
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
                current_node_id=path[0]
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

