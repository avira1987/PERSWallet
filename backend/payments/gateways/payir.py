"""Pay.ir payment gateway implementation."""
import requests
from .base import BaseGateway
from . import register_gateway


@register_gateway('payir')
class PayIRGateway(BaseGateway):
    """Pay.ir payment gateway."""

    API_URL = 'https://pay.ir/pg/'

    @property
    def name(self):
        return 'پی‌آی‌آر'

    def request_payment(self, amount, callback_url, description, order_id=None):
        try:
            response = requests.post(
                f'{self.API_URL}send',
                json={
                    'api': self.config['API_KEY'],
                    'amount': amount,
                    'redirect': callback_url,
                    'description': description,
                },
                timeout=10
            )
            data = response.json()
            if data.get('status') == 1:
                token = data['token']
                return {
                    'success': True,
                    'authority': token,
                    'payment_url': f'{self.API_URL}{token}',
                    'error': None,
                }
            return {
                'success': False, 'authority': None, 'payment_url': None,
                'error': data.get('errorMessage', 'Unknown error'),
            }
        except Exception as e:
            return {'success': False, 'authority': None, 'payment_url': None, 'error': str(e)}

    def verify_payment(self, authority, amount):
        try:
            response = requests.post(
                f'{self.API_URL}verify',
                json={'api': self.config['API_KEY'], 'token': authority},
                timeout=10
            )
            data = response.json()
            if data.get('status') == 1:
                return {
                    'success': True,
                    'ref_id': str(data.get('transId', '')),
                    'error': None,
                }
            return {'success': False, 'ref_id': None, 'error': data.get('errorMessage', 'Verification failed')}
        except Exception as e:
            return {'success': False, 'ref_id': None, 'error': str(e)}
