# trips/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',views.driver_dashboard,name='driver_dashboard'),
    path('trips/',views.TripView.as_view(),name='trip-list'),
    path('trips/update-location/',views.UpdateLocationView.as_view(),name='update-location'),   # ← before <int:pk>
    path('trips/<int:pk>/',views.TripDetailView.as_view(),name='trip-detail'),
    path('trips/<int:trip_id>/cancel/',views.CancelTripView.as_view(), name='cancel-trip'),
    path('trips/<int:trip_id>/requests/',views.DriverRequestsAPIView.as_view(), name='driver-requests'),
    path('trips/<int:trip_id>/ssr/',views.driver_dashboard_ssr,name='driver-dashboard-ssr'),
    path('trips/<int:trip_id>/cancel/page/',views.cancel_trip_page,name='cancel-trip-page'),
    path('earnings/', views.driver_transaction_history, name='driver-transaction-history'),
]