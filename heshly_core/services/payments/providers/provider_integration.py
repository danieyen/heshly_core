from __future__ import annotations

from heshly_core.services.payments.providers.provider_manager import (
    ProviderManager,
)

from heshly_core.services.payments.providers.provider_models import (
    PaymentProviderType,
    ProviderPaymentRequest,
    ProviderPaymentResult,
    ProviderRefundRequest,
    ProviderRefundResult,
)


class ProviderIntegration:
    """
    Public integration point for the
    payment provider subsystem.
    """

    def __init__(
        self,
    ) -> None:

        self._manager = ProviderManager()

    @property
    def manager(
        self,
    ) -> ProviderManager:

        return self._manager

    def process_payment(
        self,
        provider: PaymentProviderType,
        request: ProviderPaymentRequest,
    ) -> ProviderPaymentResult:

        return self._manager.process_payment(
            provider,
            request,
        )

    def verify_payment(
        self,
        provider: PaymentProviderType,
        transaction_id: str,
    ) -> ProviderPaymentResult:

        return self._manager.verify_payment(
            provider,
            transaction_id,
        )

    def refund(
        self,
        provider: PaymentProviderType,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:

        return self._manager.refund(
            provider,
            request,
        )

    def health_check(
        self,
        provider: PaymentProviderType,
    ) -> bool:

        return self._manager.health_check(
            provider,
        )

    def get_provider(
        self,
        provider: PaymentProviderType,
    ):

        return self._manager.get(
            provider,
        )

    def available_providers(
        self,
    ):

        return self._manager.available_providers()