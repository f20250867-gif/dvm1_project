from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
]