"""URL patterns for the payments app."""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('request/', views.PaymentRequestView.as_view(), name='request'),
    path('verify/', views.PaymentVerifyView.as_view(), name='verify'),
    path('history/', views.PaymentHistoryView.as_view(), name='history'),
]
