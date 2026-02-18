"""Views for the wallet app."""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer


class WalletDetailView(APIView):
    """Get current user's wallet details."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            wallet = request.user.wallet
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=request.user)
        return Response(WalletSerializer(wallet).data)


class TransactionListView(generics.ListAPIView):
    """List current user's transactions with filtering."""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(wallet=self.request.user.wallet)
        tx_type = self.request.query_params.get('type')
        tx_status = self.request.query_params.get('status')
        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)
        if tx_status:
            queryset = queryset.filter(status=tx_status)
        return queryset
