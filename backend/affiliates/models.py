"""Affiliate program models."""
import uuid
import secrets
from django.db import models
from django.conf import settings


def generate_referral_code():
    """Generate a unique 8-character referral code."""
    return secrets.token_urlsafe(6)[:8].upper()


class AffiliateProfile(models.Model):
    """Affiliate profile with unique referral code."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='affiliate_profile')
    referral_code = models.CharField(max_length=20, unique=True, default=generate_referral_code)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=0.05,
        verbose_name='نرخ پورسیون',
        help_text='درصد پورسیون (مثلا 0.05 = 5%)',
    )
    is_active = models.BooleanField(default=True)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='مجموع درآمد')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پروفایل افیلیت'
        verbose_name_plural = 'پروفایل‌های افیلیت'

    def __str__(self):
        return f"{self.user.username} - {self.referral_code}"


class Referral(models.Model):
    """Referral relationship between users."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referred = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referred_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ارجاع'
        verbose_name_plural = 'ارجاعات'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(referrer=models.F('referred')),
                name='no_self_referral'
            ),
        ]

    def __str__(self):
        return f"{self.referrer.username} -> {self.referred.username}"


class Commission(models.Model):
    """Commission records from affiliate referrals."""
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('paid', 'پرداخت شده'),
        ('cancelled', 'لغو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='commissions')
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ پورسیون')
    source_transaction_amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='مبلغ تراکنش مبدا')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'پورسیون'
        verbose_name_plural = 'پورسیون‌ها'

    def __str__(self):
        return f"{self.referral.referrer.username} - {self.amount}"
