"""Tests for transfer operations."""
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.models import User
from wallet.models import Wallet


class TransferTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sender = User.objects.create_user(
            username='sender', password='StrongPass123!', email='sender@example.com'
        )
        self.receiver = User.objects.create_user(
            username='receiver', password='StrongPass123!', email='receiver@example.com'
        )
        self.sender_wallet = Wallet.objects.create(user=self.sender, balance=Decimal('1000000'))
        self.receiver_wallet = Wallet.objects.create(user=self.receiver, balance=Decimal('500000'))
        self.client.force_authenticate(user=self.sender)

    def test_transfer_success(self):
        url = reverse('transfers:send')
        response = self.client.post(url, {
            'receiver_username': 'receiver', 'amount': 200000
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_balance'], 800000)

        self.sender_wallet.refresh_from_db()
        self.receiver_wallet.refresh_from_db()
        self.assertEqual(self.sender_wallet.balance, Decimal('800000'))
        self.assertEqual(self.receiver_wallet.balance, Decimal('700000'))

    def test_transfer_insufficient_balance(self):
        url = reverse('transfers:send')
        response = self.client.post(url, {
            'receiver_username': 'receiver', 'amount': 5000000
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_to_self(self):
        url = reverse('transfers:send')
        response = self.client.post(url, {
            'receiver_username': 'sender', 'amount': 100000
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_to_nonexistent_user(self):
        url = reverse('transfers:send')
        response = self.client.post(url, {
            'receiver_username': 'ghost', 'amount': 100000
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_transfer_by_phone(self):
        self.receiver.phone_number = '09121234567'
        self.receiver.save()
        url = reverse('transfers:send')
        response = self.client.post(url, {
            'receiver_phone': '09121234567', 'amount': 100000
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_transfer_history(self):
        # Create a transfer first
        url = reverse('transfers:send')
        self.client.post(url, {
            'receiver_username': 'receiver', 'amount': 100000
        }, format='json')

        history_url = reverse('transfers:history')
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
