from django.contrib import admin
from .models import Trip
# Register your models here.
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    # Allows admin to view all active trips on the network
    list_display = ('id', 'driver', 'start_node', 'end_node', 'current_node', 'available_seats')
    list_filter = ('driver',)