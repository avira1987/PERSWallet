"""URL patterns for the transfers app."""
from django.urls import path
from . import views

app_name = 'transfers'

urlpatterns = [
    path('send/', views.TransferView.as_view(), name='send'),
    path('history/', views.TransferHistoryView.as_view(), name='history'),
    path('pro-accounts/', views.ProAccountListView.as_view(), name='pro_accounts'),
]
