"""Serializers for the accounts app."""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'national_id', 'password', 'password_confirm',
                  'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'رمزهای عبور مطابقت ندارند.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('نام کاربری یا رمز عبور اشتباه است.')
        if not user.is_active:
            raise serializers.ValidationError('حساب کاربری غیرفعال است.')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display and update."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'phone_number', 'national_id', 'is_pro', 'two_factor_enabled',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'is_pro', 'two_factor_enabled',
                           'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('رمز عبور فعلی اشتباه است.')
        return value


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup confirmation."""
    totp_code = serializers.CharField(max_length=6, min_length=6)


class TwoFactorDisableSerializer(serializers.Serializer):
    """Serializer for disabling 2FA."""
    password = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(max_length=6, min_length=6)
