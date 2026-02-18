"""Tests for wallet operations."""
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.models import User
from wallet.models import Wallet, Transaction


class WalletTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='StrongPass123!', email='test@example.com'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('1000000'))
        self.client.force_authenticate(user=self.user)

    def test_get_wallet(self):
        url = reverse('wallet:detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(response.data['balance']), 1000000)

    def test_transaction_list(self):
        Transaction.objects.create(
            wallet=self.wallet,
            transaction_type='charge',
            amount=Decimal('500000'),
            balance_after=Decimal('1500000'),
            status='completed',
        )
        url = reverse('wallet:transactions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_transaction_filter_by_type(self):
        Transaction.objects.create(
            wallet=self.wallet, transaction_type='charge',
            amount=Decimal('500000'), balance_after=Decimal('1500000'), status='completed',
        )
        Transaction.objects.create(
            wallet=self.wallet, transaction_type='transfer_out',
            amount=Decimal('100000'), balance_after=Decimal('900000'), status='completed',
        )
        url = reverse('wallet:transactions')
        response = self.client.get(url, {'type': 'charge'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
