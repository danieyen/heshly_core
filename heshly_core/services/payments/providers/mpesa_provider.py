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


class MPesaProvider(PaymentProviderInterface):
    """
    Safaricom M-Pesa payment provider.
    """

    def __init__(self) -> None:

        self._configuration = ProviderConfiguration(
            provider=PaymentProviderType.MPESA,
            enabled=True,
            sandbox=True,
        )

        self._info = ProviderInfo(
            provider=PaymentProviderType.MPESA,
            name="Safaricom M-Pesa",
            payment_method=PaymentMethod.MPESA,
            capabilities=ProviderCapabilities(
                supports_refunds=True,
                supports_partial_payments=False,
                supports_payment_links=False,
                supports_webhooks=True,
                supports_recurring_payments=False,
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
            transaction_id="MPESA-TXN-001",
            message="STK Push request initiated.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.MPESA,
        )

    def verify_payment(
        self,
        transaction_id: str,
    ) -> ProviderPaymentResult:

        result = PaymentResult(
            success=True,
            status=PaymentStatus.PAID,
            transaction_id=transaction_id,
            message="M-Pesa payment verified.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.MPESA,
        )

    def refund(
        self,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:

        result = RefundResult(
            success=True,
            message="M-Pesa refund processed.",
        )

        return ProviderRefundResult(
            result=result,
            provider=PaymentProviderType.MPESA,
        )

    def health_check(
        self,
    ) -> bool:

        return True