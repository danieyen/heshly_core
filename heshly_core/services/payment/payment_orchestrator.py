from __future__ import annotations

from heshly_core.models.payment import Payment

from heshly_core.services.payment.providers.provider_factory import (
    PaymentProviderFactory,
)


class PaymentOrchestrator:

    def initiate(
        self,
        payment: Payment,
    ):
        provider = PaymentProviderFactory.create(
            payment.provider
        )

        return provider.initiate_payment(
            payment
        )

    def verify(
        self,
        payment: Payment,
    ):
        provider = PaymentProviderFactory.create(
            payment.provider
        )

        return provider.verify_payment(
            payment.provider_reference or ""
        )

    def refund(
        self,
        payment: Payment,
    ):
        provider = PaymentProviderFactory.create(
            payment.provider
        )

        return provider.refund(
            payment
        )
