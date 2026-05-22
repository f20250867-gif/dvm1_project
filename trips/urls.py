from django.urls import path
from . import views

urlpatterns = [
    path('trips/',          views.TripView.as_view(),       name='trip-list'),
    path('trips/<int:pk>/', views.TripDetailView.as_view(), name='trip-detail'),
]