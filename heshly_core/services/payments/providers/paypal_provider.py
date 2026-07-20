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


class PayPalProvider(PaymentProviderInterface):
    """
    PayPal payment provider.
    """

    def __init__(self) -> None:

        self._configuration = ProviderConfiguration(
            provider=PaymentProviderType.PAYPAL,
            enabled=True,
            sandbox=True,
        )

        self._info = ProviderInfo(
            provider=PaymentProviderType.PAYPAL,
            name="PayPal",
            payment_method=PaymentMethod.PAYPAL,
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
            transaction_id="PAYPAL-TXN-001",
            payment_url="https://www.paypal.com/checkoutnow",
            message="PayPal payment created.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.PAYPAL,
        )

    def verify_payment(
        self,
        transaction_id: str,
    ) -> ProviderPaymentResult:

        result = PaymentResult(
            success=True,
            status=PaymentStatus.PAID,
            transaction_id=transaction_id,
            message="PayPal payment verified.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.PAYPAL,
        )

    def refund(
        self,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:

        result = RefundResult(
            success=True,
            message="PayPal refund processed.",
        )

        return ProviderRefundResult(
            result=result,
            provider=PaymentProviderType.PAYPAL,
        )

    def health_check(
        self,
    ) -> bool:

        return True