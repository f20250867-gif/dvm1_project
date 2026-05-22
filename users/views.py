from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegisterForm
from .models import User
from django.contrib.auth.decorators import login_required
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
    if user.role == User.Role.DRIVER:
        return redirect('driver_dashboard')
    elif user.role == User.Role.PASSENGER:
        return redirect('passenger_dashboard')
    else:
        return redirect('/admin/')