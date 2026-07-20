from __future__ import annotations

from heshly_core.services.payments.providers.erpnext_provider import (
    ERPNextProvider,
)
from heshly_core.services.payments.providers.mpesa_provider import (
    MPesaProvider,
)
from heshly_core.services.payments.providers.paypal_provider import (
    PayPalProvider,
)
from heshly_core.services.payments.providers.provider_interface import (
    PaymentProviderInterface,
)
from heshly_core.services.payments.providers.provider_models import (
    PaymentProviderType,
)
from heshly_core.services.payments.providers.stripe_provider import (
    StripeProvider,
)


class ProviderFactory:
    """
    Factory responsible for creating
    payment provider instances.
    """

    @staticmethod
    def create(
        provider: PaymentProviderType,
    ) -> PaymentProviderInterface:

        if provider == PaymentProviderType.ERPNEXT:
            return ERPNextProvider()

        if provider == PaymentProviderType.STRIPE:
            return StripeProvider()

        if provider == PaymentProviderType.PAYPAL:
            return PayPalProvider()

        if provider == PaymentProviderType.MPESA:
            return MPesaProvider()

        raise ValueError(
            f"Unsupported payment provider: {provider}"
        )