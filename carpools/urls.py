from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.passenger_dashboard,  name='passenger_dashboard'),
    path('offer/', views.MakeOfferView.as_view(),   name='make-offer'),
    path('confirm/<int:offer_id>/', views.AcceptOfferView.as_view(), name='confirm-offer'),
    path('offers/<int:request_id>/', views.ViewOffersView.as_view(),  name='view-offers'),      
    path('cancel/<int:request_id>/', views.CancelRequestView.as_view(), name='cancel-request'), 
    path('offers/page/<int:request_id>/', views.view_offers_page,            name='view-offers-page'),
    path('confirm/page/<int:offer_id>/', views.confirm_offer_page,          name='confirm-offer-page'),
    path('cancel/page/<int:request_id>/', views.cancel_request_page,         name='cancel-request-page'),
    path('offer/<int:request_id>/',views.make_offer_page, name='make-offer-page'),
    path('wallet/topup/', views.wallet_topup_page, name='wallet-topup-page'),
    path('wallet/transactions/', views.transaction_history, name='transaction-history'),
]