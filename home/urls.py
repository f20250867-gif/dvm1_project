from django.urls import path
from . import views # . is current directory

urlpatterns = [
    path('', views.home, name='carpool-home'),
]