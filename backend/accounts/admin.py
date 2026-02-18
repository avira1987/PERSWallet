"""Admin configuration for accounts."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'phone_number', 'is_pro', 'two_factor_enabled', 'is_active']
    list_filter = ['is_pro', 'two_factor_enabled', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone_number', 'national_id']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات اضافی', {'fields': ('phone_number', 'national_id', 'is_pro', 'two_factor_enabled')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['user', 'action', 'details', 'ip_address', 'created_at']
