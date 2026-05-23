from rest_framework import serializers
from .models import Trip

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"
        read_only_fields = ['driver', 'route', 'visited_nodes', 'available_seats', 'current_node','status', 'created at']