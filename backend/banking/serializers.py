"""Serializers for the banking app."""
import re
from rest_framework import serializers
from .models import RefundRequest


class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['id', 'amount', 'iban', 'account_holder_name', 'description',
                  'status', 'tracking_code', 'created_at', 'processed_at']
        read_only_fields = ['id', 'status', 'tracking_code', 'created_at', 'processed_at']

    def validate_iban(self, value):
        """Validate Iranian IBAN format (IR + 24 digits)."""
        value = value.strip().upper()
        if not re.match(r'^IR\d{24}$', value):
            raise serializers.ValidationError('شماره شبا نامعتبر است. فرمت صحیح: IR + 24 رقم')
        return value

    def validate_amount(self, value):
        if value < 50000:
            raise serializers.ValidationError('حداقل مبلغ بازپرداخت ۵۰,۰۰۰ ریال است.')
        return value


class RefundStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['id', 'amount', 'iban', 'status', 'tracking_code',
                  'error_message', 'created_at', 'processed_at']
        read_only_fields = fields
