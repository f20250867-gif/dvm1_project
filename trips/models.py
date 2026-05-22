from django.db import models
from network.views import Node
from users.models import User
#Trip Model
class Trip(models.Model):

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    start_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="trip_start"
    )

    end_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name="trip_end"
    )

    current_node = models.ForeignKey(
        Node,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trip_current"
    )
    route = models.JSONField(null=True, blank=True)#storing the route
    visited_nodes = models.JSONField(default=list, blank=True)#to keep track of visited nodes during the trip

    max_passengers = models.IntegerField()

    available_seats = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} {self.start_node}->{self.end_node}"