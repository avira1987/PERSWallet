"""Abstract base class for payment gateways."""
from abc import ABC, abstractmethod


class BaseGateway(ABC):
    """Abstract payment gateway interface.
    All gateways must implement these methods.
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def request_payment(self, amount: int, callback_url: str, description: str, order_id: str = None) -> dict:
        """Request a new payment.
        Returns: {'success': bool, 'authority': str, 'payment_url': str, 'error': str|None}
        """
        pass

    @abstractmethod
    def verify_payment(self, authority: str, amount: int) -> dict:
        """Verify a completed payment.
        Returns: {'success': bool, 'ref_id': str, 'error': str|None}
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Gateway name for display."""
        pass
