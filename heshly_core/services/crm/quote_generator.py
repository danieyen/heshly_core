from __future__ import annotations

from datetime import date
from uuid import uuid4

from heshly_core.models.quote import (
    Quote,
    QuoteItem,
    QuoteStatus,
)


class QuoteGenerator:
    """
    Generates customer quotations.

    Responsible only for creating Quote objects.
    Persistence is handled by QuoteRepository.
    """

    def __init__(self):

        self._counter = 1

    # =====================================================
    # Public API
    # =====================================================

    def create(

        self,

        business_id: str,

        customer_id: str,

        title: str,

        opportunity_id: str | None = None,

        currency: str = "KES",

        expiry_date: date | None = None,

        notes: str | None = None,

        terms: str | None = None,

        created_by: str | None = None,

    ) -> Quote:

        quote = Quote(

            quote_id=self._generate_quote_id(),

            business_id=business_id,

            customer_id=customer_id,

            opportunity_id=opportunity_id,

            quote_number=self._generate_quote_number(),

            title=title,

            currency=currency,

            status=QuoteStatus.DRAFT,

            expiry_date=expiry_date,

            notes=notes,

            terms=terms,

            created_by=created_by,

        )

        return quote

    # =====================================================
    # Quote Items
    # =====================================================

    def add_item(

        self,

        quote: Quote,

        item: QuoteItem,

    ) -> Quote:

        quote.add_item(item)

        return quote

    def remove_item(

        self,

        quote: Quote,

        item_id: str,

    ) -> bool:

        return quote.remove_item(item_id)

    # =====================================================
    # Totals
    # =====================================================

    def subtotal(

        self,

        quote: Quote,

    ) -> float:

        return quote.subtotal

    def discount_total(

        self,

        quote: Quote,

    ) -> float:

        return quote.discount_total

    def tax_total(

        self,

        quote: Quote,

    ) -> float:

        return quote.tax_total

    def grand_total(

        self,

        quote: Quote,

    ) -> float:

        return quote.grand_total

    # =====================================================
    # Private Helpers
    # =====================================================

    def _generate_quote_id(self) -> str:

        return f"QUOTE-{uuid4().hex[:10].upper()}"

    def _generate_quote_number(self) -> str:

        number = f"QT-{self._counter:06d}"

        self._counter += 1

        return number