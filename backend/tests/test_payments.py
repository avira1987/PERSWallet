"""Tests for payment gateway integration."""
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.models import User
from wallet.models import Wallet
from payments.models import PaymentRecord
from payments.gateways.base import BaseGateway


class PaymentGatewayBaseTest(TestCase):
    """Test that abstract gateway interface works correctly."""

    def test_cannot_instantiate_base(self):
        with self.assertRaises(TypeError):
            BaseGateway({})


class PaymentRequestTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='StrongPass123!', email='test@example.com'
        )
        self.wallet = Wallet.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

    @patch('payments.views.get_gateway')
    def test_payment_request_success(self, mock_get_gateway):
        mock_gateway = MagicMock()
        mock_gateway.request_payment.return_value = {
            'success': True,
            'authority': 'test-authority-123',
            'payment_url': 'https://gateway.example.com/pay/123',
            'error': None,
        }
        mock_get_gateway.return_value = mock_gateway

        url = reverse('payments:request')
        response = self.client.post(url, {'amount': 100000}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)

    @patch('payments.views.get_gateway')
    def test_payment_request_gateway_error(self, mock_get_gateway):
        mock_gateway = MagicMock()
        mock_gateway.request_payment.return_value = {
            'success': False,
            'authority': None,
            'payment_url': None,
            'error': 'Gateway error',
        }
        mock_get_gateway.return_value = mock_gateway

        url = reverse('payments:request')
        response = self.client.post(url, {'amount': 100000}, format='json')
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    def test_payment_request_invalid_amount(self):
        url = reverse('payments:request')
        response = self.client.post(url, {'amount': 100}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaymentVerifyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='StrongPass123!', email='test@example.com'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))
        self.client.force_authenticate(user=self.user)

    @patch('payments.views.get_gateway')
    def test_verify_success(self, mock_get_gateway):
        payment = PaymentRecord.objects.create(
            user=self.user, gateway='zarinpal', amount=100000,
            authority='test-auth-123', status='redirected'
        )
        mock_gateway = MagicMock()
        mock_gateway.verify_payment.return_value = {
            'success': True, 'ref_id': 'REF-123', 'error': None
        }
        mock_gateway.name = 'زرین‌پال'
        mock_get_gateway.return_value = mock_gateway

        url = reverse('payments:verify')
        response = self.client.post(url, {'authority': 'test-auth-123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_balance'], 100000)

    def test_verify_not_found(self):
        url = reverse('payments:verify')
        response = self.client.post(url, {'authority': 'nonexistent'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
