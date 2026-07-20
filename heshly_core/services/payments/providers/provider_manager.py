from __future__ import annotations

from heshly_core.services.payments.providers.provider_factory import (
    ProviderFactory,
)

from heshly_core.services.payments.providers.provider_interface import (
    PaymentProviderInterface,
)

from heshly_core.services.payments.providers.provider_models import (
    PaymentProviderType,
    ProviderPaymentRequest,
    ProviderPaymentResult,
    ProviderRefundRequest,
    ProviderRefundResult,
)


class ProviderManager:
    """
    Coordinates payment providers.

    Creates providers on demand and
    reuses them for subsequent requests.
    """

    def __init__(self) -> None:

        self._providers: dict[
            PaymentProviderType,
            PaymentProviderInterface,
        ] = {}

    def get(
        self,
        provider: PaymentProviderType,
    ) -> PaymentProviderInterface:

        if provider not in self._providers:
            self._providers[provider] = (
                ProviderFactory.create(provider)
            )

        return self._providers[provider]

    def process_payment(
        self,
        provider: PaymentProviderType,
        request: ProviderPaymentRequest,
    ) -> ProviderPaymentResult:

        return self.get(provider).process_payment(
            request,
        )

    def verify_payment(
        self,
        provider: PaymentProviderType,
        transaction_id: str,
    ) -> ProviderPaymentResult:

        return self.get(provider).verify_payment(
            transaction_id,
        )

    def refund(
        self,
        provider: PaymentProviderType,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:

        return self.get(provider).refund(
            request,
        )

    def health_check(
        self,
        provider: PaymentProviderType,
    ) -> bool:

        return self.get(provider).health_check()

    def available_providers(
        self,
    ) -> list[PaymentProviderType]:

        return list(self._providers.keys())