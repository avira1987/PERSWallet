"""Admin configuration for wallet."""
from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__phone_number']
    list_filter = ['is_active']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['wallet__user__username', 'reference_id']
    readonly_fields = ['id', 'wallet', 'transaction_type', 'amount', 'balance_after',
                       'status', 'reference_id', 'metadata', 'created_at']
