"""Admin configuration for banking."""
from django.contrib import admin
from .models import RefundRequest


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'iban', 'status', 'tracking_code', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'iban', 'tracking_code']
