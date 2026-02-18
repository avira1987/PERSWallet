"""Admin configuration for payments."""
from django.contrib import admin
from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'gateway', 'amount', 'status', 'ref_id', 'created_at']
    list_filter = ['gateway', 'status', 'created_at']
    search_fields = ['user__username', 'authority', 'ref_id']
    readonly_fields = ['id', 'user', 'gateway', 'amount', 'authority', 'ref_id',
                       'status', 'error_message', 'created_at']
