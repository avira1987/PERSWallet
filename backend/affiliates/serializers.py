"""Serializers for the affiliates app."""
from rest_framework import serializers
from .models import AffiliateProfile, Referral, Commission


class AffiliateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    referrals_count = serializers.SerializerMethodField()

    class Meta:
        model = AffiliateProfile
        fields = ['id', 'username', 'referral_code', 'commission_rate',
                  'is_active', 'total_earnings', 'referrals_count', 'created_at']
        read_only_fields = fields

    def get_referrals_count(self, obj):
        return Referral.objects.filter(referrer=obj.user).count()


class ReferralSerializer(serializers.ModelSerializer):
    referrer_username = serializers.CharField(source='referrer.username', read_only=True)
    referred_username = serializers.CharField(source='referred.username', read_only=True)

    class Meta:
        model = Referral
        fields = ['id', 'referrer_username', 'referred_username', 'created_at']
        read_only_fields = fields


class CommissionSerializer(serializers.ModelSerializer):
    referred_username = serializers.CharField(source='referral.referred.username', read_only=True)

    class Meta:
        model = Commission
        fields = ['id', 'referred_username', 'amount', 'source_transaction_amount',
                  'status', 'created_at']
        read_only_fields = fields
