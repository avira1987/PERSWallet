"""URL patterns for the affiliates app."""
from django.urls import path
from . import views

app_name = 'affiliates'

urlpatterns = [
    path('profile/', views.AffiliateProfileView.as_view(), name='profile'),
    path('referrals/', views.ReferralListView.as_view(), name='referrals'),
    path('commissions/', views.CommissionListView.as_view(), name='commissions'),
]
