from __future__ import annotations

from heshly_core.models.quote import (
    Quote,
    QuoteItem,
)


class PricingRules:
    """
    Pricing rules engine.

    Responsible for:

    - Percentage discounts
    - Fixed discounts
    - Bulk discounts
    - Loyalty discounts
    - Coupon discounts
    - Tax calculations
    - Grand total calculations
    """

    DEFAULT_TAX_RATE = 16.0

    # =====================================================
    # ITEM RULES
    # =====================================================

    def apply_percentage_discount(
        self,
        item: QuoteItem,
        percent: float,
    ) -> QuoteItem:

        if not 0 <= percent <= 100:
            raise ValueError(
                "Discount must be between 0 and 100."
            )

        item.discount = percent

        return item

    def apply_fixed_discount(
        self,
        item: QuoteItem,
        amount: float,
    ) -> QuoteItem:

        if amount < 0:
            raise ValueError(
                "Discount cannot be negative."
            )

        subtotal = item.quantity * item.unit_price

        if subtotal == 0:
            item.discount = 0
            return item

        item.discount = min(
            100,
            (amount / subtotal) * 100,
        )

        return item

    def apply_bulk_discount(
        self,
        item: QuoteItem,
        minimum_quantity: float,
        discount: float,
    ) -> QuoteItem:

        if item.quantity >= minimum_quantity:

            self.apply_percentage_discount(
                item,
                discount,
            )

        return item

    def apply_loyalty_discount(
        self,
        item: QuoteItem,
        customer_level: str,
    ) -> QuoteItem:

        levels = {

            "bronze": 2,

            "silver": 5,

            "gold": 10,

            "platinum": 15,

        }

        percent = levels.get(
            customer_level.lower(),
            0,
        )

        self.apply_percentage_discount(
            item,
            percent,
        )

        return item

    def apply_coupon(
        self,
        item: QuoteItem,
        coupon_code: str,
    ) -> QuoteItem:

        coupons = {

            "WELCOME10": 10,

            "SAVE20": 20,

            "VIP30": 30,

        }

        discount = coupons.get(
            coupon_code.upper(),
            0,
        )

        self.apply_percentage_discount(
            item,
            discount,
        )

        return item

    def apply_tax(
        self,
        item: QuoteItem,
        tax_rate: float | None = None,
    ) -> QuoteItem:

        item.tax_rate = (

            tax_rate

            if tax_rate is not None

            else self.DEFAULT_TAX_RATE

        )

        return item

    # =====================================================
    # QUOTE RULES
    # =====================================================

    def apply_quote_discount(
        self,
        quote: Quote,
        percent: float,
    ) -> Quote:

        for item in quote.items:

            self.apply_percentage_discount(
                item,
                percent,
            )

        return quote

    def apply_quote_tax(
        self,
        quote: Quote,
        tax_rate: float | None = None,
    ) -> Quote:

        for item in quote.items:

            self.apply_tax(
                item,
                tax_rate,
            )

        return quote

    # =====================================================
    # TOTALS
    # =====================================================

    def subtotal(
        self,
        quote: Quote,
    ) -> float:

        return quote.subtotal

    def total_discount(
        self,
        quote: Quote,
    ) -> float:

        return quote.discount_total

    def taxable_total(
        self,
        quote: Quote,
    ) -> float:

        return quote.taxable_total

    def total_tax(
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
    # VALIDATION
    # =====================================================

    def validate(
        self,
        quote: Quote,
    ) -> list[str]:

        errors: list[str] = []

        if len(quote.items) == 0:

            errors.append(
                "Quote must contain at least one item."
            )

        for item in quote.items:

            if item.quantity <= 0:

                errors.append(

                    f"{item.name}: quantity must be greater than zero."

                )

            if item.unit_price < 0:

                errors.append(

                    f"{item.name}: unit price cannot be negative."

                )

            if not 0 <= item.discount <= 100:

                errors.append(

                    f"{item.name}: invalid discount."

                )

            if item.tax_rate < 0:

                errors.append(

                    f"{item.name}: invalid tax rate."

                )

        return errors

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(
        self,
        quote: Quote,
    ) -> dict:

        return {

            "items": len(quote.items),

            "subtotal": quote.subtotal,

            "discount": quote.discount_total,

            "taxable": quote.taxable_total,

            "tax": quote.tax_total,

            "grand_total": quote.grand_total,

        }