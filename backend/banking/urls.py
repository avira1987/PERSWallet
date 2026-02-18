"""URL patterns for the banking app."""
from django.urls import path
from . import views

app_name = 'banking'

urlpatterns = [
    path('refund/', views.RefundRequestView.as_view(), name='refund_request'),
    path('refunds/', views.RefundListView.as_view(), name='refund_list'),
    path('admin/refunds/', views.AdminRefundListView.as_view(), name='admin_refund_list'),
    path('admin/refunds/<uuid:refund_id>/', views.AdminRefundProcessView.as_view(), name='admin_refund_process'),
]
