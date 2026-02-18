"""Serializers for the wallet app."""
from rest_framework import serializers
from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'username', 'balance', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'balance', 'is_active', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'balance_after', 'status',
                  'description', 'reference_id', 'created_at']
        read_only_fields = fields
