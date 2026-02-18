"""Payment gateway registry and factory."""
from django.conf import settings

_gateway_registry = {}


def register_gateway(name):
    """Decorator to register a payment gateway."""
    def decorator(cls):
        _gateway_registry[name] = cls
        return cls
    return decorator


def get_gateway(name=None):
    """Get the active payment gateway instance."""
    if name is None:
        name = settings.ACTIVE_GATEWAY
    gateway_class = _gateway_registry.get(name)
    if gateway_class is None:
        raise ValueError(f"Gateway '{name}' is not registered. Available: {list(_gateway_registry.keys())}")
    config = settings.PAYMENT_GATEWAYS.get(name, {})
    return gateway_class(config)


# Import all gateways to trigger registration
from . import zarinpal, idpay, payir, nextpay  # noqa: F401, E402
