"""Views for the accounts app."""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, AuditLog
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    TwoFactorSetupSerializer,
    TwoFactorDisableSerializer,
)
from .totp import generate_totp_secret, get_totp_uri, generate_qr_code_base64, verify_totp


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Create wallet for user
        from wallet.models import Wallet
        Wallet.objects.create(user=user)
        # Create affiliate code
        from affiliates.models import AffiliateProfile
        AffiliateProfile.objects.create(user=user)
        # Handle referral code if provided
        referral_code = request.data.get('referral_code')
        if referral_code:
            from affiliates.models import Referral
            try:
                referrer_profile = AffiliateProfile.objects.get(referral_code=referral_code)
                if referrer_profile.user != user:
                    Referral.objects.create(referrer=referrer_profile.user, referred=user)
            except AffiliateProfile.DoesNotExist:
                pass
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'ثبت‌نام با موفقیت انجام شد.',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login endpoint with optional 2FA."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Check 2FA
        if user.two_factor_enabled:
            totp_code = request.data.get('totp_code', '')
            if not totp_code:
                return Response({
                    'requires_2fa': True,
                    'message': 'کد احراز هویت دو مرحله‌ای مورد نیاز است.'
                }, status=status.HTTP_200_OK)
            if not verify_totp(user.totp_secret, totp_code):
                return Response({
                    'error': 'کد احراز هویت دو مرحله‌ای نامعتبر است.'
                }, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        # Audit log
        AuditLog.objects.create(
            user=user, action='login',
            ip_address=get_client_ip(request),
            details={'method': 'password+2fa' if user.two_factor_enabled else 'password'}
        )

        return Response({
            'message': 'ورود موفقیت‌آمیز.',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': UserProfileSerializer(user).data,
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """View and update user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        AuditLog.objects.create(
            user=self.request.user, action='profile_update',
            ip_address=get_client_ip(self.request),
        )


class ChangePasswordView(APIView):
    """Change user password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        AuditLog.objects.create(
            user=request.user, action='password_change',
            ip_address=get_client_ip(request),
        )
        return Response({'message': 'رمز عبور با موفقیت تغییر یافت.'})


class TwoFactorSetupView(APIView):
    """Setup 2FA - Generate secret and QR code."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Generate a new TOTP secret and QR code."""
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, request.user.username)
        qr_base64 = generate_qr_code_base64(uri)
        # Store secret temporarily (will be confirmed in POST)
        request.user.totp_secret = secret
        request.user.save(update_fields=['totp_secret'])
        return Response({
            'secret': secret,
            'qr_code': f'data:image/png;base64,{qr_base64}',
            'message': 'کد QR را با اپلیکیشن Authenticator اسکن کنید و کد تایید را وارد نمایید.',
        })

    def post(self, request):
        """Confirm 2FA setup with a TOTP code."""
        serializer = TwoFactorSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.totp_secret:
            return Response({'error': 'ابتدا باید QR code را دریافت کنید.'}, status=status.HTTP_400_BAD_REQUEST)
        if not verify_totp(user.totp_secret, serializer.validated_data['totp_code']):
            return Response({'error': 'کد نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled'])
        AuditLog.objects.create(
            user=user, action='2fa_enable',
            ip_address=get_client_ip(request),
        )
        return Response({'message': 'احراز هویت دو مرحله‌ای با موفقیت فعال شد.'})


class TwoFactorDisableView(APIView):
    """Disable 2FA."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['password']):
            return Response({'error': 'رمز عبور اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)
        if not verify_totp(user.totp_secret, serializer.validated_data['totp_code']):
            return Response({'error': 'کد نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)
        user.two_factor_enabled = False
        user.totp_secret = None
        user.save(update_fields=['two_factor_enabled', 'totp_secret'])
        AuditLog.objects.create(
            user=user, action='2fa_disable',
            ip_address=get_client_ip(request),
        )
        return Response({'message': 'احراز هویت دو مرحله‌ای غیرفعال شد.'})
