from django.urls import path
from .views import WalletBalanceView, WalletTopUpView, DriverEarningsView
urlpatterns = [

path('wallet/balance/',  WalletBalanceView.as_view(),  name='wallet-balance'),
path('driver/earnings/', DriverEarningsView.as_view(), name='driver-earnings'),
]