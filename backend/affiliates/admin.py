"""Admin configuration for affiliates."""
from django.contrib import admin
from .models import AffiliateProfile, Referral, Commission


@admin.register(AffiliateProfile)
class AffiliateProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'referral_code', 'commission_rate', 'total_earnings', 'is_active']
    search_fields = ['user__username', 'referral_code']
    list_filter = ['is_active']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred', 'created_at']
    search_fields = ['referrer__username', 'referred__username']


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['referral', 'amount', 'source_transaction_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
