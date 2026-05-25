from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegisterForm
from .models import User
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status                   
from rest_framework.permissions import IsAuthenticated

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')
            return redirect('login') 
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form' : form})


@login_required
def role_redirect(request):
    user = request.user

    if not user.role or user.role == '':  
        return redirect('select-role')

    if user.role == 'DRIVER':
        return redirect('driver_dashboard')
    elif user.role == 'PASSENGER':
        return redirect('passenger_dashboard')
    else:
        return redirect('/admin/')

class WalletBalanceView(APIView):
    """Passenger can check their wallet balance"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'PASSENGER':
            return Response(
                {"error": "Only passengers have a wallet."},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            "username":       request.user.username,
            "wallet_balance": request.user.wallet_balance
        }, status=status.HTTP_200_OK)


class DriverEarningsView(APIView):
    """Driver can check their earnings"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'DRIVER':
            return Response(
                {"error": "Only drivers can view earnings."},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            "username": request.user.username,
            "earnings": request.user.wallet_balance
        }, status=status.HTTP_200_OK)

@login_required
def select_role(request):
    # if user already has role skip this page
    if request.user.role:
        return redirect('role-redirect')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ['DRIVER', 'PASSENGER']:
            request.user.role = role
            request.user.save()
            return redirect('role-redirect')

    return render(request, 'users/select_role.html')