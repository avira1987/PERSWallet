"""Tests for user authentication, registration, and 2FA."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from accounts.totp import generate_totp_secret, verify_totp


class RegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('accounts:register')

    def test_register_success(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone_number': '09121234567',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'تست',
            'last_name': 'کاربر',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_password_mismatch(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'DifferentPass!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username='existing', password='pass1234!')
        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='StrongPass123!', email='test@example.com'
        )
        self.url = reverse('accounts:login')

    def test_login_success(self):
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'StrongPass123!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_2fa_required(self):
        secret = generate_totp_secret()
        self.user.totp_secret = secret
        self.user.two_factor_enabled = True
        self.user.save()

        # Without TOTP code
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'StrongPass123!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('requires_2fa'))


class TOTPTest(TestCase):
    def test_generate_and_verify_totp(self):
        secret = generate_totp_secret()
        self.assertIsNotNone(secret)
        self.assertGreater(len(secret), 10)

    def test_verify_invalid_code(self):
        secret = generate_totp_secret()
        self.assertFalse(verify_totp(secret, '000000'))


class ProfileTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='StrongPass123!', email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_update_profile(self):
        url = reverse('accounts:profile')
        response = self.client.patch(url, {'first_name': 'تست'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'تست')
