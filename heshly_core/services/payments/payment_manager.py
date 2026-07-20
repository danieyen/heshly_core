from __future__ import annotations

from heshly_core.models.payment import (
    Invoice,
    PaymentRequest,
    PaymentResult,
    PaymentStatus,
    Quote,
    RefundRequest,
)

from heshly_core.services.payments.invoice_manager import (
    InvoiceManager,
)

from heshly_core.services.payments.payment_confirmation import (
    PaymentConfirmation,
)

from heshly_core.services.payments.payment_conversation_flow import (
    PaymentConversationFlow,
)

from heshly_core.services.payments.payment_links import (
    PaymentLinks,
)

from heshly_core.services.payments.providers.provider_integration import (
    ProviderIntegration,
)

from heshly_core.services.payments.providers.provider_models import (
    PaymentProviderType,
    ProviderConfiguration,
    ProviderPaymentRequest,
    ProviderRefundRequest,
)

from heshly_core.services.payments.quote_manager import (
    QuoteManager,
)

from heshly_core.services.payments.refund_manager import (
    RefundManager,
)


class PaymentManager:
    """
    Coordinates the complete payment subsystem.

    Higher-level modules should communicate
    with payments through this class rather
    than individual managers.
    """

    def __init__(
        self,
    ) -> None:

        self._quote = QuoteManager()

        self._invoice = InvoiceManager()

        self._links = PaymentLinks()

        self._confirmation = PaymentConfirmation()

        self._providers = ProviderIntegration()

        self._refunds = RefundManager()

        self._conversation = PaymentConversationFlow()

    #
    # Public Components
    #

    @property
    def quote(
        self,
    ) -> QuoteManager:

        return self._quote

    @property
    def invoice(
        self,
    ) -> InvoiceManager:

        return self._invoice

    @property
    def links(
        self,
    ) -> PaymentLinks:

        return self._links

    @property
    def confirmation(
        self,
    ) -> PaymentConfirmation:

        return self._confirmation

    @property
    def providers(
        self,
    ) -> ProviderIntegration:

        return self._providers

    @property
    def refunds(
        self,
    ) -> RefundManager:

        return self._refunds

    @property
    def conversation(
        self,
    ) -> PaymentConversationFlow:

        return self._conversation

    #
    # Quote
    #

    def create_quote(
        self,
        quote: Quote,
    ) -> Quote:

        return self._quote.create(
            quote,
        )

    #
    # Invoice
    #

    def create_invoice(
        self,
        invoice: Invoice,
    ) -> Invoice:

        return self._invoice.create(
            invoice,
        )

    #
    # Payment Links
    #

    def create_payment_link(
        self,
        invoice: Invoice,
    ) -> str:

        return self._links.generate(
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

        provider_request = ProviderPaymentRequest(
            payment=request,
            configuration=ProviderConfiguration(
                provider=provider,
            ),
        )

        return self._providers.process_payment(
            provider,
            provider_request,
        )

    def verify_payment(
        self,
        provider: PaymentProviderType,
        transaction_id: str,
    ):

        return self._providers.verify_payment(
            provider,
            transaction_id,
        )

    def confirm_payment(
        self,
        invoice: Invoice,
        result: PaymentResult,
    ) -> Invoice:

        return self._confirmation.confirm(
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

        provider_request = ProviderRefundRequest(
            refund=request,
            configuration=ProviderConfiguration(
                provider=provider,
            ),
        )

        return self._providers.refund(
            provider,
            provider_request,
        )

    #
    # Conversation
    #

    def payment_message(
        self,
        status: PaymentStatus,
    ) -> str:

        return self._conversation.next_step(
            status,
        )