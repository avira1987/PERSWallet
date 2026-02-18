"""Views for the transfers app."""
from decimal import Decimal
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Transfer
from .serializers import TransferRequestSerializer, TransferRecordSerializer, ProAccountSerializer
from accounts.models import User, AuditLog
from wallet.models import Wallet, Transaction


class TransferView(APIView):
    """Transfer balance to another user."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = TransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sender = request.user
        amount = Decimal(str(serializer.validated_data['amount']))
        description = serializer.validated_data.get('description', '')

        # Find receiver
        receiver = None
        if serializer.validated_data.get('receiver_username'):
            try:
                receiver = User.objects.get(username=serializer.validated_data['receiver_username'])
            except User.DoesNotExist:
                return Response({'error': 'کاربر گیرنده یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        elif serializer.validated_data.get('receiver_phone'):
            try:
                receiver = User.objects.get(phone_number=serializer.validated_data['receiver_phone'])
            except User.DoesNotExist:
                return Response({'error': 'کاربر با این شماره تلفن یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        if receiver == sender:
            return Response({'error': 'امکان انتقال به خود وجود ندارد.'}, status=status.HTTP_400_BAD_REQUEST)

        if not receiver.is_active:
            return Response({'error': 'حساب گیرنده غیرفعال است.'}, status=status.HTTP_400_BAD_REQUEST)

        # Lock wallets in consistent order to prevent deadlocks
        wallet_ids = sorted([sender.wallet.id, receiver.wallet.id])
        wallets = Wallet.objects.select_for_update().filter(id__in=wallet_ids)
        wallets_dict = {w.user_id: w for w in wallets}
        sender_wallet = wallets_dict[sender.id]
        receiver_wallet = wallets_dict[receiver.id]

        if sender_wallet.balance < amount:
            return Response({'error': 'موجودی کافی نیست.'}, status=status.HTTP_400_BAD_REQUEST)

        if not sender_wallet.is_active or not receiver_wallet.is_active:
            return Response({'error': 'یکی از کیف پول‌ها غیرفعال است.'}, status=status.HTTP_400_BAD_REQUEST)

        # Perform transfer
        sender_wallet.balance -= amount
        sender_wallet.save()
        receiver_wallet.balance += amount
        receiver_wallet.save()

        # Create transfer record
        transfer = Transfer.objects.create(
            sender=sender, receiver=receiver,
            amount=amount, status='completed', description=description,
        )

        # Create transaction records
        Transaction.objects.create(
            wallet=sender_wallet, transaction_type='transfer_out',
            amount=amount, balance_after=sender_wallet.balance,
            status='completed', description=f'انتقال به {receiver.username}',
            reference_id=f'TRF-{transfer.id}',
        )
        Transaction.objects.create(
            wallet=receiver_wallet, transaction_type='transfer_in',
            amount=amount, balance_after=receiver_wallet.balance,
            status='completed', description=f'دریافت از {sender.username}',
            reference_id=f'TRF-{transfer.id}-IN',
        )

        # Audit logs
        AuditLog.objects.create(
            user=sender, action='transfer',
            details={'to': receiver.username, 'amount': int(amount), 'transfer_id': str(transfer.id)},
        )

        return Response({
            'message': 'انتقال با موفقیت انجام شد.',
            'transfer': TransferRecordSerializer(transfer).data,
            'new_balance': int(sender_wallet.balance),
        })


class TransferHistoryView(generics.ListAPIView):
    """List user's transfer history (sent and received)."""
    serializer_class = TransferRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        direction = self.request.query_params.get('direction', 'all')
        if direction == 'sent':
            return Transfer.objects.filter(sender=user)
        elif direction == 'received':
            return Transfer.objects.filter(receiver=user)
        return Transfer.objects.filter(Q(sender=user) | Q(receiver=user))


class ProAccountListView(generics.ListAPIView):
    """List all pro accounts for the dedicated pro charge page."""
    serializer_class = ProAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_pro=True, is_active=True).values(
            'id', 'username', 'first_name', 'last_name'
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return Response(list(queryset))
