"""NextPay payment gateway implementation."""
import requests
from .base import BaseGateway
from . import register_gateway


@register_gateway('nextpay')
class NextPayGateway(BaseGateway):
    """NextPay payment gateway."""

    API_URL = 'https://nextpay.org/nx/gateway/'

    @property
    def name(self):
        return 'نکست‌پی'

    def request_payment(self, amount, callback_url, description, order_id=None):
        try:
            response = requests.post(
                f'{self.API_URL}token',
                json={
                    'api_key': self.config['API_KEY'],
                    'amount': amount,
                    'callback_uri': callback_url,
                    'order_id': order_id or '',
                },
                timeout=10
            )
            data = response.json()
            if data.get('code') == -1:
                trans_id = data['trans_id']
                return {
                    'success': True,
                    'authority': trans_id,
                    'payment_url': f'{self.API_URL}payment/{trans_id}',
                    'error': None,
                }
            return {
                'success': False, 'authority': None, 'payment_url': None,
                'error': data.get('message', 'Unknown error'),
            }
        except Exception as e:
            return {'success': False, 'authority': None, 'payment_url': None, 'error': str(e)}

    def verify_payment(self, authority, amount):
        try:
            response = requests.post(
                f'{self.API_URL}verify',
                json={
                    'api_key': self.config['API_KEY'],
                    'amount': amount,
                    'trans_id': authority,
                },
                timeout=10
            )
            data = response.json()
            if data.get('code') == 0:
                return {
                    'success': True,
                    'ref_id': str(data.get('Shaparak_Ref_Id', '')),
                    'error': None,
                }
            return {'success': False, 'ref_id': None, 'error': data.get('message', 'Verification failed')}
        except Exception as e:
            return {'success': False, 'ref_id': None, 'error': str(e)}
