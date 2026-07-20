from __future__ import annotations

from heshly_core.models.quote import (
    Quote,
    QuoteItem,
)


class QuoteItems:
    """
    Handles all quote item operations.

    Responsible for:
        - Adding items
        - Removing items
        - Updating items
        - Quantity changes
        - Price changes
        - Discounts
        - Tax rates
    """

    # =====================================================
    # Add Item
    # =====================================================

    def add_item(
        self,
        quote: Quote,
        item: QuoteItem,
    ) -> Quote:

        quote.items.append(item)

        return quote

    # =====================================================
    # Remove Item
    # =====================================================

    def remove_item(
        self,
        quote: Quote,
        item_id: str,
    ) -> bool:

        for index, item in enumerate(quote.items):

            if item.item_id == item_id:

                del quote.items[index]

                return True

        return False

    # =====================================================
    # Replace Item
    # =====================================================

    def update_item(
        self,
        quote: Quote,
        updated_item: QuoteItem,
    ) -> bool:

        for index, item in enumerate(quote.items):

            if item.item_id == updated_item.item_id:

                quote.items[index] = updated_item

                return True

        return False

    # =====================================================
    # Quantity
    # =====================================================

    def set_quantity(
        self,
        quote: Quote,
        item_id: str,
        quantity: float,
    ) -> bool:

        if quantity < 0:

            raise ValueError(
                "Quantity cannot be negative."
            )

        item = self.get_item(
            quote,
            item_id,
        )

        if item is None:

            return False

        item.quantity = quantity

        return True

    # =====================================================
    # Unit Price
    # =====================================================

    def set_unit_price(
        self,
        quote: Quote,
        item_id: str,
        unit_price: float,
    ) -> bool:

        if unit_price < 0:

            raise ValueError(
                "Unit price cannot be negative."
            )

        item = self.get_item(
            quote,
            item_id,
        )

        if item is None:

            return False

        item.unit_price = unit_price

        return True

    # =====================================================
    # Discount
    # =====================================================

    def set_discount(
        self,
        quote: Quote,
        item_id: str,
        discount: float,
    ) -> bool:

        if not 0 <= discount <= 100:

            raise ValueError(
                "Discount must be between 0 and 100."
            )

        item = self.get_item(
            quote,
            item_id,
        )

        if item is None:

            return False

        item.discount = discount

        return True

    # =====================================================
    # Tax
    # =====================================================

    def set_tax_rate(
        self,
        quote: Quote,
        item_id: str,
        tax_rate: float,
    ) -> bool:

        if tax_rate < 0:

            raise ValueError(
                "Tax rate cannot be negative."
            )

        item = self.get_item(
            quote,
            item_id,
        )

        if item is None:

            return False

        item.tax_rate = tax_rate

        return True

    # =====================================================
    # Retrieval
    # =====================================================

    def get_item(
        self,
        quote: Quote,
        item_id: str,
    ) -> QuoteItem | None:

        for item in quote.items:

            if item.item_id == item_id:

                return item

        return None

    def list_items(
        self,
        quote: Quote,
    ) -> list[QuoteItem]:

        return quote.items

    def item_count(
        self,
        quote: Quote,
    ) -> int:

        return len(quote.items)

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
    # Clear
    # =====================================================

    def clear_items(
        self,
        quote: Quote,
    ) -> None:

        quote.items.clear()