"""
URL configuration for dvm1_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name = 'register'),
    path('role-redirect/', user_views.role_redirect, name='role-redirect'),
    path('login/', auth_views.LoginView.as_view(template_name = 'users/login.html'), name = 'login'),
    path('logout/', auth_views.LogoutView.as_view(template_name = 'users/logout.html'), name = 'logout'),
    path('', include('home.urls')),
    path('network/', include('network.urls')),
    path('driver/', include('trips.urls')),       
    path('passenger/', include('carpools.urls')), 
    path('api/token/', obtain_auth_token, name='api-token'),
    path('accounts/', include('allauth.urls')),
    path('select-role/', user_views.select_role, name='select-role'),
]
