from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('',views.TripView.as_view(),name='trip-list'),
    path('<int:pk>/',views.TripDetailView.as_view(),name='trip-detail'),
    path('<int:trip_id>/cancel/',views.CancelTripView.as_view(),name='cancel-trip'),
    path('update-location/',views.UpdateLocationView.as_view(),  name='update-location'),
    path('<int:trip_id>/requests/',views.DriverRequestsAPIView.as_view(),name='driver-requests'),
]