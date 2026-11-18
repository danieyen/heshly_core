from __future__ import annotations

from heshly_core.models.payment import PaymentProvider

from heshly_core.services.payment.providers.mpesa_provider import (
    MpesaProvider,
)


class PaymentProviderFactory:

    @staticmethod
    def create(provider: PaymentProvider):

        if provider == PaymentProvider.MPESA:
            return MpesaProvider()

        raise ValueError(
            f"Unsupported payment provider: {provider.value}"
        )
