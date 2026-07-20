from __future__ import annotations

from datetime import datetime

from heshly_core.models.payment import (
    Invoice,
    PaymentItem,
    PaymentStatus,
    Quote,
)


class QuoteManager:
    """
    Handles quote creation and management.
    """

    def create(
        self,
        quote: Quote,
    ) -> Quote:
        """
        Initialize a quote.
        """

        quote.updated_at = datetime.utcnow()

        return quote

    def add_item(
        self,
        quote: Quote,
        item: PaymentItem,
    ) -> Quote:

        quote.items.append(item)

        quote.updated_at = datetime.utcnow()

        return quote

    def remove_item(
        self,
        quote: Quote,
        index: int,
    ) -> Quote:

        if 0 <= index < len(quote.items):
            quote.items.pop(index)

        quote.updated_at = datetime.utcnow()

        return quote

    def calculate_total(
        self,
        quote: Quote,
    ):

        return quote.total

    def is_expired(
        self,
        quote: Quote,
    ) -> bool:

        if quote.expires_at is None:
            return False

        return datetime.utcnow() > quote.expires_at

    def convert_to_invoice(
        self,
        quote: Quote,
        invoice_id: str,
    ) -> Invoice:

        return Invoice(
            invoice_id=invoice_id,
            customer_id=quote.customer_id,
            currency=quote.currency,
            items=list(quote.items),
            quote_id=quote.quote_id,
            status=PaymentStatus.DRAFT,
        )