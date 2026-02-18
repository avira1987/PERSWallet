"""Views for payment gateway integration."""
import uuid
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PaymentRecord
from .serializers import PaymentRequestSerializer, PaymentVerifySerializer, PaymentRecordSerializer
from .gateways import get_gateway
from wallet.models import Transaction
from accounts.models import AuditLog


class PaymentRequestView(APIView):
    """Initiate a payment through the selected gateway."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        gateway_name = serializer.validated_data.get('gateway') or settings.ACTIVE_GATEWAY

        try:
            gateway = get_gateway(gateway_name)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        order_id = str(uuid.uuid4())[:8]
        callback_url = f"{settings.PAYMENT_CALLBACK_BASE_URL}/payment/verify?gateway={gateway_name}"

        result = gateway.request_payment(
            amount=amount,
            callback_url=callback_url,
            description=f'شارژ کیف پول - {request.user.username}',
            order_id=order_id,
        )

        # Create payment record
        payment = PaymentRecord.objects.create(
            user=request.user,
            gateway=gateway_name,
            amount=amount,
            authority=result.get('authority'),
            status='redirected' if result['success'] else 'failed',
            error_message=result.get('error'),
        )

        if result['success']:
            return Response({
                'payment_url': result['payment_url'],
                'authority': result['authority'],
                'payment_id': str(payment.id),
            })
        return Response({
            'error': result.get('error', 'خطا در اتصال به درگاه پرداخت'),
        }, status=status.HTTP_502_BAD_GATEWAY)


class PaymentVerifyView(APIView):
    """Verify a payment callback from the gateway."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        authority = serializer.validated_data['authority']

        try:
            payment = PaymentRecord.objects.select_for_update().get(
                authority=authority, user=request.user
            )
        except PaymentRecord.DoesNotExist:
            return Response({'error': 'رکورد پرداخت یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status == 'verified':
            return Response({'error': 'این پرداخت قبلا تایید شده است.'}, status=status.HTTP_400_BAD_REQUEST)

        gateway = get_gateway(payment.gateway)
        result = gateway.verify_payment(authority=authority, amount=int(payment.amount))

        if result['success']:
            payment.status = 'verified'
            payment.ref_id = result['ref_id']
            payment.save()

            # Credit wallet
            wallet = request.user.wallet
            wallet.balance += payment.amount
            wallet.save()

            # Create transaction record
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='charge',
                amount=payment.amount,
                balance_after=wallet.balance,
                status='completed',
                description=f'شارژ از درگاه {gateway.name}',
                reference_id=result['ref_id'],
                metadata={'gateway': payment.gateway, 'payment_id': str(payment.id)},
            )

            # Audit log
            AuditLog.objects.create(
                user=request.user, action='charge',
                details={'amount': int(payment.amount), 'gateway': payment.gateway, 'ref_id': result['ref_id']},
            )

            # Process affiliate commission
            _process_affiliate_commission(request.user, payment.amount)

            return Response({
                'message': 'پرداخت با موفقیت تایید شد.',
                'ref_id': result['ref_id'],
                'amount': int(payment.amount),
                'new_balance': int(wallet.balance),
            })
        else:
            payment.status = 'failed'
            payment.error_message = result.get('error')
            payment.save()
            return Response({
                'error': 'تایید پرداخت ناموفق بود.',
                'detail': result.get('error'),
            }, status=status.HTTP_400_BAD_REQUEST)


def _process_affiliate_commission(user, amount):
    """Process affiliate commission for a successful charge."""
    from affiliates.models import Referral, Commission
    try:
        referral = Referral.objects.select_related('referrer').get(referred=user)
        commission_rate = Decimal(str(settings.AFFILIATE_COMMISSION_RATE))
        commission_amount = amount * commission_rate

        if commission_amount > 0:
            Commission.objects.create(
                referral=referral,
                amount=commission_amount,
                source_transaction_amount=amount,
            )
            # Credit referrer wallet
            referrer_wallet = referral.referrer.wallet
            referrer_wallet.balance += commission_amount
            referrer_wallet.save()
            Transaction.objects.create(
                wallet=referrer_wallet,
                transaction_type='commission',
                amount=commission_amount,
                balance_after=referrer_wallet.balance,
                status='completed',
                description=f'پورسیون افیلیت از {user.username}',
            )
    except Referral.DoesNotExist:
        pass


class PaymentHistoryView(generics.ListAPIView):
    """List user's payment records."""
    serializer_class = PaymentRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentRecord.objects.filter(user=self.request.user)
