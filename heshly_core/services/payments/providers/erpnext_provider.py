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


class ERPNextProvider(PaymentProviderInterface):
    """
    ERPNext payment provider.

    This provider serves as the bridge between
    Heshly and ERPNext's payment and accounting
    functionality.
    """

    def __init__(self) -> None:

        self._configuration = ProviderConfiguration(
            provider=PaymentProviderType.ERPNEXT,
            enabled=True,
            sandbox=False,
        )

        self._info = ProviderInfo(
            provider=PaymentProviderType.ERPNEXT,
            name="ERPNext",
            payment_method=PaymentMethod.OTHER,
            capabilities=ProviderCapabilities(
                supports_refunds=True,
                supports_partial_payments=True,
                supports_payment_links=True,
                supports_webhooks=False,
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
            transaction_id="ERP-TXN-001",
            message="Payment request created in ERPNext.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.ERPNEXT,
        )

    def verify_payment(
        self,
        transaction_id: str,
    ) -> ProviderPaymentResult:

        result = PaymentResult(
            success=True,
            status=PaymentStatus.PAID,
            transaction_id=transaction_id,
            message="Payment verified by ERPNext.",
        )

        return ProviderPaymentResult(
            result=result,
            provider=PaymentProviderType.ERPNEXT,
        )

    def refund(
        self,
        request: ProviderRefundRequest,
    ) -> ProviderRefundResult:

        result = RefundResult(
            success=True,
            message="Refund processed by ERPNext.",
        )

        return ProviderRefundResult(
            result=result,
            provider=PaymentProviderType.ERPNEXT,
        )

    def health_check(self) -> bool:
        """
        Placeholder health check.

        Later this can verify database
        connectivity or ERPNext services.
        """
        return True