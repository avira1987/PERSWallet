"""Views for the banking API (refunds)."""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import RefundRequest
from .serializers import RefundRequestSerializer, RefundStatusSerializer
from wallet.models import Transaction
from accounts.models import AuditLog


class RefundRequestView(APIView):
    """Request a refund to bank account."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = Decimal(str(serializer.validated_data['amount']))
        wallet = request.user.wallet

        # Lock wallet
        from wallet.models import Wallet
        wallet = Wallet.objects.select_for_update().get(id=wallet.id)

        if wallet.balance < amount:
            return Response({'error': 'موجودی کافی نیست.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deduct from wallet
        wallet.balance -= amount
        wallet.save()

        # Create refund request
        refund = serializer.save(user=request.user)

        # Create transaction record
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='refund',
            amount=amount,
            balance_after=wallet.balance,
            status='pending',
            description=f'بازپرداخت به شبا {refund.iban}',
            reference_id=f'RFD-{refund.id}',
        )

        # Audit log
        AuditLog.objects.create(
            user=request.user, action='refund',
            details={'amount': int(amount), 'iban': refund.iban, 'refund_id': str(refund.id)},
        )

        return Response({
            'message': 'درخواست بازپرداخت ثبت شد.',
            'refund': RefundStatusSerializer(refund).data,
        }, status=status.HTTP_201_CREATED)


class RefundListView(generics.ListAPIView):
    """List user's refund requests."""
    serializer_class = RefundStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RefundRequest.objects.filter(user=self.request.user)


class AdminRefundProcessView(APIView):
    """Admin endpoint to process/update refund status."""
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def patch(self, request, refund_id):
        try:
            refund = RefundRequest.objects.select_for_update().get(id=refund_id)
        except RefundRequest.DoesNotExist:
            return Response({'error': 'درخواست بازپرداخت یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        tracking_code = request.data.get('tracking_code')

        if new_status not in ['processing', 'completed', 'failed', 'rejected']:
            return Response({'error': 'وضعیت نامعتبر.'}, status=status.HTTP_400_BAD_REQUEST)

        # If rejecting/failing, refund the wallet
        if new_status in ['failed', 'rejected'] and refund.status not in ['failed', 'rejected', 'completed']:
            wallet = refund.user.wallet
            from wallet.models import Wallet
            wallet = Wallet.objects.select_for_update().get(id=wallet.id)
            wallet.balance += refund.amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='charge',
                amount=refund.amount,
                balance_after=wallet.balance,
                status='completed',
                description=f'بازگشت مبلغ بازپرداخت رد شده',
                reference_id=f'RFD-RETURN-{refund.id}',
            )

        refund.status = new_status
        if tracking_code:
            refund.tracking_code = tracking_code
        if new_status in ['completed', 'failed', 'rejected']:
            refund.processed_at = timezone.now()
        if request.data.get('error_message'):
            refund.error_message = request.data['error_message']
        refund.save()

        return Response({
            'message': 'وضعیت بازپرداخت بروزرسانی شد.',
            'refund': RefundStatusSerializer(refund).data,
        })


class AdminRefundListView(generics.ListAPIView):
    """Admin view: list all refund requests."""
    serializer_class = RefundStatusSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = RefundRequest.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
