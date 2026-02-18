"""Banking API models for refund operations."""
import uuid
from django.db import models
from django.conf import settings


class RefundRequest(models.Model):
    """Refund request to user's bank account via Paya/Satna."""
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('rejected', 'رد شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='refund_requests')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ (ریال)')
    iban = models.CharField(max_length=26, verbose_name='شماره شبا')
    account_holder_name = models.CharField(max_length=100, verbose_name='نام صاحب حساب')
    description = models.TextField(blank=True, default='بازپرداخت از کیف پول')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_code = models.CharField(max_length=100, blank=True, null=True, verbose_name='کد پیگیری')
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'درخواست بازپرداخت'
        verbose_name_plural = 'درخواست‌های بازپرداخت'

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"
