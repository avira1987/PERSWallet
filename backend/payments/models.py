"""Payment record models."""
import uuid
from django.db import models
from django.conf import settings


class PaymentRecord(models.Model):
    """Record of payment gateway interactions."""
    STATUS_CHOICES = [
        ('initiated', 'آغاز شده'),
        ('redirected', 'هدایت شده'),
        ('verified', 'تایید شده'),
        ('failed', 'ناموفق'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    gateway = models.CharField(max_length=20, verbose_name='درگاه')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ (ریال)')
    authority = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    description = models.TextField(blank=True, default='شارژ کیف پول')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'رکورد پرداخت'
        verbose_name_plural = 'رکوردهای پرداخت'

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"
