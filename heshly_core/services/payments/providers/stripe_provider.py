from __future__ import annotations

from heshly_core.models.payment import (
    PaymentMethod,
    PaymentResult,
    PaymentStatus,
    RefundResult,
)

from heshly_core.services.payments.providers.provider_interface import (
    PaymentProviderInterface,
)

from heshly_core.services.payments.providers.provider_models import (
    PaymentProviderType,
    ProviderCapabilities,
    ProviderConfiguration,
    ProviderInfo,
    ProviderPaymentRequest,
    ProviderPaymentResult,
    ProviderRefundRequest,
    ProviderRefundResult,
)


class StripeProvider(PaymentProviderInterface):
    """
    Stripe payment provider.
    """

    def __init__(self) -> None:

        self._configuration = ProviderConfiguration(
            provider=PaymentProviderType.STRIPE,
            enabled=True,
            sandbox=True,
        )

        self._info = ProviderInfo(
            provider=PaymentProviderType.STRIPE,
            name="Stripe",
            payment_method=PaymentMethod.STRIPE,
            capabilities=ProviderCapabilities(
                supports_refunds=True,
                supports_partial_payments=True,
                supports_payment_links=True,
                supports_webhooks=True,
                supports_recurring_payments=True,
            ),
        )

    @property
    def info(self) -> ProviderInfo:
        return self._info

    @property
    def configuration(self) -> ProviderConfiguration:
        return self._configuration

    def process_payment(
        self,
        request: ProviderPaymentRequest,
    ) -> ProviderPaymentResult:

        result = PaymentResult(
            success=True,
            status=PaymentStatus.PENDING,
            transaction_id="STRIPE-TXN-001",
            payment_url="https://checkout.stripe.com/pay/example",
            message="Stripe Checkout session created.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.STRIPE,
        )

    def verify_payment(
        self,
        transaction_id: str,
    ) -> ProviderPaymentResult:

        result = PaymentResult(
            success=True,
            status=PaymentStatus.PAID,
            transaction_id=transaction_id,
            message="Stripe payment verified.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.STRIPE,
        )

    def refund(
        self,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:

        result = RefundResult(
            success=True,
            message="Stripe refund processed.",
        )

        return ProviderRefundResult(
            result=result,
            provider=PaymentProviderType.STRIPE,
        )

    def health_check(self) -> bool:
        return True