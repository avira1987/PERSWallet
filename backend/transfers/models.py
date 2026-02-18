"""Transfer models for sending balance between users."""
import uuid
from django.db import models
from django.conf import settings


class Transfer(models.Model):
    """Record of balance transfers between users."""
    STATUS_CHOICES = [
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transfers')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ (ریال)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'انتقال'
        verbose_name_plural = 'انتقال‌ها'

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.amount}"
