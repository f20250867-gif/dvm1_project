from django.contrib import admin
from .models import RideRequest, RideOffer


@admin.register(RideRequest)
class RideRequestAdmin(admin.ModelAdmin):
    list_display  = ('id', 'passenger', 'pickup_node', 'drop_node', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('passenger__username',)


@admin.register(RideOffer)
class RideOfferAdmin(admin.ModelAdmin):
    list_display  = ('id', 'trip', 'ride_request', 'detour', 'proposed_fare', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('trip__driver__username',)