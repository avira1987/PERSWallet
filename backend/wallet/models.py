"""Wallet and Transaction models."""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings


class Wallet(models.Model):
    """User wallet with balance tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=15, decimal_places=0, default=Decimal('0'), verbose_name='موجودی (ریال)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'

    def __str__(self):
        return f"{self.user.username} - {self.balance} ریال"


class Transaction(models.Model):
    """Record of all wallet transactions."""
    TYPE_CHOICES = [
        ('charge', 'شارژ'),
        ('transfer_in', 'دریافت انتقال'),
        ('transfer_out', 'ارسال انتقال'),
        ('refund', 'بازپرداخت'),
        ('commission', 'پورسیون افیلیت'),
    ]
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ (ریال)')
    balance_after = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='موجودی بعد از تراکنش')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, default='')
    reference_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - {self.amount}"
