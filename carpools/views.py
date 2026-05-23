from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def passenger_dashboard(request):
    return render(request, 'carpools/passenger_dashboard.html')