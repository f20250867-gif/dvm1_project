from django.db import models
from users.models import User
from network.models import Node
from trips.models import Trip


class RideRequest(models.Model):

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('matched',   'Matched'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ride_requests'
    )

    pickup_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='pickup_requests'
    )

    drop_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='drop_requests'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger} | {self.pickup_node} → {self.drop_node} | {self.status}"


class RideOffer(models.Model):

    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='trip_offers'
    )

    ride_request = models.ForeignKey(
        RideRequest,
        on_delete=models.CASCADE,
        related_name='request_offers'
    )

    detour        = models.FloatField(default=0)
    proposed_fare = models.FloatField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer by {self.trip.driver} for {self.ride_request.passenger} | {self.status}"