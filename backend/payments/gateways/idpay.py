"""IDPay payment gateway implementation."""
import requests
from .base import BaseGateway
from . import register_gateway


@register_gateway('idpay')
class IDPayGateway(BaseGateway):
    """IDPay payment gateway."""

    SANDBOX_API = 'https://api.idpay.ir/v1.1/payment'
    PRODUCTION_API = 'https://api.idpay.ir/v1.1/payment'

    @property
    def name(self):
        return 'آیدی‌پی'

    def _headers(self):
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.config['API_KEY'],
        }
        if self.config.get('SANDBOX', True):
            headers['X-SANDBOX'] = '1'
        return headers

    def request_payment(self, amount, callback_url, description, order_id=None):
        try:
            response = requests.post(
                self.PRODUCTION_API,
                json={
                    'order_id': order_id or '',
                    'amount': amount,
                    'callback': callback_url,
                    'desc': description,
                },
                headers=self._headers(),
                timeout=10
            )
            data = response.json()
            if response.status_code == 201:
                return {
                    'success': True,
                    'authority': data['id'],
                    'payment_url': data['link'],
                    'error': None,
                }
            return {
                'success': False, 'authority': None, 'payment_url': None,
                'error': data.get('error_message', 'Unknown error'),
            }
        except Exception as e:
            return {'success': False, 'authority': None, 'payment_url': None, 'error': str(e)}

    def verify_payment(self, authority, amount):
        try:
            response = requests.post(
                f'{self.PRODUCTION_API}/verify',
                json={'id': authority, 'order_id': ''},
                headers=self._headers(),
                timeout=10
            )
            data = response.json()
            if data.get('status') == 100:
                return {
                    'success': True,
                    'ref_id': str(data.get('track_id', '')),
                    'error': None,
                }
            return {'success': False, 'ref_id': None, 'error': data.get('error_message', 'Verification failed')}
        except Exception as e:
            return {'success': False, 'ref_id': None, 'error': str(e)}
