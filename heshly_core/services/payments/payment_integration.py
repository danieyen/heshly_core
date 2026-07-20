from __future__ import annotations

from heshly_core.models.payment import (
    Invoice,
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    Quote,
    RefundRequest,
)

from heshly_core.services.payments.payment_manager import (
    PaymentManager,
)

from heshly_core.services.payments.providers.provider_models import (
    PaymentProviderType,
)


class PaymentIntegration:
    """
    Public integration point for the
    Payments module.

    Other modules should communicate
    with the payments subsystem
    through this class.
    """

    def __init__(
        self,
    ) -> None:

        self._manager = PaymentManager()

    @property
    def manager(
        self,
    ) -> PaymentManager:

        return self._manager

    #
    # Quote
    #

    def create_quote(
        self,
        quote: Quote,
    ) -> Quote:

        return self._manager.create_quote(
            quote,
        )

    #
    # Invoice
    #

    def create_invoice(
        self,
        invoice: Invoice,
    ) -> Invoice:

        return self._manager.create_invoice(
            invoice,
        )

    #
    # Payment Links
    #

    def create_payment_link(
        self,
        invoice: Invoice,
    ) -> str:

        return self._manager.create_payment_link(
            invoice,
        )

    #
    # Payments
    #

    def process_payment(
        self,
        provider: PaymentProviderType,
        request: PaymentRequest,
    ):

        return self._manager.process_payment(
            provider,
            request,
        )

    def verify_payment(
        self,
        provider: PaymentProviderType,
        transaction_id: str,
    ):

        return self._manager.verify_payment(
            provider,
            transaction_id,
        )

    def confirm_payment(
        self,
        invoice: Invoice,
        result: PaymentResult,
    ) -> Invoice:

        return self._manager.confirm_payment(
            invoice,
            result,
        )

    #
    # Refunds
    #

    def refund(
        self,
        provider: PaymentProviderType,
        request: RefundRequest,
    ):

        return self._manager.refund(
            provider,
            request,
        )

    #
    # Conversation
    #

    def payment_message(
        self,
        status: PaymentStatus,
    ) -> str:

        return self._manager.payment_message(
            status,
        )