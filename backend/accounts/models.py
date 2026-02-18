"""Custom User model with Argon2 hashing and 2FA support."""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model with phone, national ID, pro status, and 2FA."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True, verbose_name='شماره تلفن')
    national_id = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name='کد ملی')
    is_pro = models.BooleanField(default=False, verbose_name='حساب پرو')
    two_factor_enabled = models.BooleanField(default=False, verbose_name='احراز هویت دو مرحله‌ای')
    totp_secret = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.username


class AuditLog(models.Model):
    """Audit log for tracking sensitive operations."""
    ACTION_CHOICES = [
        ('login', 'ورود'),
        ('logout', 'خروج'),
        ('password_change', 'تغییر رمز'),
        ('2fa_enable', 'فعال‌سازی 2FA'),
        ('2fa_disable', 'غیرفعال‌سازی 2FA'),
        ('profile_update', 'بروزرسانی پروفایل'),
        ('charge', 'شارژ'),
        ('transfer', 'انتقال'),
        ('refund', 'بازپرداخت'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'لاگ'
        verbose_name_plural = 'لاگ‌ها'

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"
