from rest_framework import serializers
from .models import RideRequest,RideOffer



class RideRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model  = RideRequest
        fields = '__all__'
        read_only_fields = ['passenger', 'status', 'created_at']
        depth  = 1 

class RideOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model        = RideOffer
        fields       = '__all__'
        read_only_fields = ['trip', 'ride_request', 'detour', 'proposed_fare', 'status', 'created_at']
        depth        = 1