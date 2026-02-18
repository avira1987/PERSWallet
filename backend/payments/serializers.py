"""Serializers for the payments app."""
from rest_framework import serializers
from .models import PaymentRecord


class PaymentRequestSerializer(serializers.Serializer):
    """Serializer for initiating a payment."""
    amount = serializers.IntegerField(min_value=10000, max_value=500000000,
                                       help_text='مبلغ به ریال (حداقل ۱۰,۰۰۰ ریال)')
    gateway = serializers.CharField(required=False, allow_blank=True,
                                     help_text='نام درگاه (اختیاری، پیش‌فرض از تنظیمات)')


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying a payment callback."""
    authority = serializers.CharField()
    status = serializers.CharField(required=False)


class PaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = ['id', 'gateway', 'amount', 'authority', 'ref_id', 'status',
                  'description', 'created_at']
        read_only_fields = fields
