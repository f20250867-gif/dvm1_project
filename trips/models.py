from django.db import models
from users.models import User
from network.models import Node

class Trip(models.Model):

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        ACTIVE    = 'ACTIVE',    'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    start_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='trip_start'
    )

    end_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='trip_end'
    )

    current_node = models.ForeignKey(
        Node,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trip_current'
    )

    status = models.CharField(           
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    route = models.JSONField(default=list, blank=True)   
    visited_nodes = models.JSONField(default=list, blank=True)
    max_passengers = models.IntegerField()
    available_seats = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} | {self.start_node} → {self.end_node} | {self.status}"


