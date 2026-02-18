"""Serializers for the transfers app."""
from rest_framework import serializers
from .models import Transfer
from accounts.serializers import UserProfileSerializer


class TransferRequestSerializer(serializers.Serializer):
    """Serializer for requesting a transfer."""
    receiver_username = serializers.CharField(required=False)
    receiver_phone = serializers.CharField(required=False)
    amount = serializers.IntegerField(min_value=1000, max_value=100000000)
    description = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if not attrs.get('receiver_username') and not attrs.get('receiver_phone'):
            raise serializers.ValidationError('نام کاربری یا شماره تلفن گیرنده الزامی است.')
        return attrs


class TransferRecordSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Transfer
        fields = ['id', 'sender_username', 'receiver_username', 'amount',
                  'status', 'description', 'created_at']
        read_only_fields = fields


class ProAccountSerializer(serializers.Serializer):
    """Serializer for listing pro accounts."""
    id = serializers.UUIDField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
