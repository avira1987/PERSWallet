"""Admin configuration for transfers."""
from django.contrib import admin
from .models import Transfer


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__username', 'receiver__username']
    readonly_fields = ['id', 'sender', 'receiver', 'amount', 'status', 'description', 'created_at']
