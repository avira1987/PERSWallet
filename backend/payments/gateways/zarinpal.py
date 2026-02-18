"""ZarinPal payment gateway implementation."""
import requests
from .base import BaseGateway
from . import register_gateway


@register_gateway('zarinpal')
class ZarinPalGateway(BaseGateway):
    """ZarinPal payment gateway (Shaparak)."""

    SANDBOX_API = 'https://sandbox.zarinpal.com/pg/v4/payment/'
    PRODUCTION_API = 'https://api.zarinpal.com/pg/v4/payment/'
    SANDBOX_START_PAY = 'https://sandbox.zarinpal.com/pg/StartPay/'
    PRODUCTION_START_PAY = 'https://www.zarinpal.com/pg/StartPay/'

    @property
    def name(self):
        return 'زرین‌پال'

    @property
    def api_url(self):
        return self.SANDBOX_API if self.config.get('SANDBOX', True) else self.PRODUCTION_API

    @property
    def start_pay_url(self):
        return self.SANDBOX_START_PAY if self.config.get('SANDBOX', True) else self.PRODUCTION_START_PAY

    def request_payment(self, amount, callback_url, description, order_id=None):
        try:
            response = requests.post(
                f'{self.api_url}request.json',
                json={
                    'merchant_id': self.config['MERCHANT_ID'],
                    'amount': amount,
                    'callback_url': callback_url,
                    'description': description,
                },
                timeout=10
            )
            data = response.json()
            if data.get('data', {}).get('code') == 100:
                authority = data['data']['authority']
                return {
                    'success': True,
                    'authority': authority,
                    'payment_url': f'{self.start_pay_url}{authority}',
                    'error': None,
                }
            return {
                'success': False,
                'authority': None,
                'payment_url': None,
                'error': str(data.get('errors', 'Unknown error')),
            }
        except Exception as e:
            return {'success': False, 'authority': None, 'payment_url': None, 'error': str(e)}

    def verify_payment(self, authority, amount):
        try:
            response = requests.post(
                f'{self.api_url}verify.json',
                json={
                    'merchant_id': self.config['MERCHANT_ID'],
                    'amount': amount,
                    'authority': authority,
                },
                timeout=10
            )
            data = response.json()
            if data.get('data', {}).get('code') in [100, 101]:
                return {
                    'success': True,
                    'ref_id': str(data['data']['ref_id']),
                    'error': None,
                }
            return {'success': False, 'ref_id': None, 'error': str(data.get('errors', 'Verification failed'))}
        except Exception as e:
            return {'success': False, 'ref_id': None, 'error': str(e)}
