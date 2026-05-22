from django.urls import path
from . import views

urlpatterns = [
    path('nodes/',        views.NodeView.as_view(),       name='node-list'),
    path('nodes/<int:pk>/', views.NodeDetailView.as_view(), name='node-detail'),
    path('edges/',        views.EdgeView.as_view(),       name='edge-list'),
    path('edges/<int:pk>/', views.EdgeDetailView.as_view(), name='edge-detail'),
]