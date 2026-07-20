from __future__ import annotations

from heshly_core.models.quote import (
    Quote,
    QuoteItem,
)


class DiscountRules:
    """
    Discount Rules Engine.

    Responsible for:

    - Item discounts
    - Quote discounts
    - Customer tier discounts
    - Coupon discounts
    - Volume discounts
    - Seasonal discounts
    - Maximum discount enforcement
    """

    MAX_DISCOUNT = 50.0

    CUSTOMER_DISCOUNTS = {

        "standard": 0,

        "bronze": 3,

        "silver": 5,

        "gold": 10,

        "platinum": 15,

    }

    COUPONS = {

        "WELCOME10": 10,

        "SAVE20": 20,

        "VIP25": 25,

    }

    # =====================================================
    # Validation
    # =====================================================

    def validate_discount(
        self,
        discount: float,
    ) -> float:

        if discount < 0:

            raise ValueError(
                "Discount cannot be negative."
            )

        if discount > self.MAX_DISCOUNT:

            raise ValueError(

                f"Maximum allowed discount is {self.MAX_DISCOUNT}%."

            )

        return discount

    # =====================================================
    # Item Discount
    # =====================================================

    def apply_item_discount(
        self,
        item: QuoteItem,
        discount: float,
    ) -> QuoteItem:

        item.discount = self.validate_discount(
            discount
        )

        return item

    # =====================================================
    # Quote Discount
    # =====================================================

    def apply_quote_discount(
        self,
        quote: Quote,
        discount: float,
    ) -> Quote:

        discount = self.validate_discount(
            discount
        )

        for item in quote.items:

            item.discount = discount

        return quote

    # =====================================================
    # Customer Tier
    # =====================================================

    def apply_customer_discount(
        self,
        quote: Quote,
        tier: str,
    ) -> Quote:

        discount = self.CUSTOMER_DISCOUNTS.get(

            tier.lower(),

            0,

        )

        return self.apply_quote_discount(

            quote,

            discount,

        )

    # =====================================================
    # Coupon
    # =====================================================

    def apply_coupon(
        self,
        quote: Quote,
        code: str,
    ) -> bool:

        discount = self.COUPONS.get(

            code.upper()

        )

        if discount is None:

            return False

        self.apply_quote_discount(

            quote,

            discount,

        )

        return True

    # =====================================================
    # Volume Discount
    # =====================================================

    def apply_volume_discount(
        self,
        item: QuoteItem,
    ) -> QuoteItem:

        quantity = item.quantity

        if quantity >= 100:

            item.discount = 20

        elif quantity >= 50:

            item.discount = 15

        elif quantity >= 20:

            item.discount = 10

        elif quantity >= 10:

            item.discount = 5

        return item

    # =====================================================
    # Seasonal Discount
    # =====================================================

    def apply_seasonal_discount(
        self,
        quote: Quote,
        percent: float,
    ) -> Quote:

        percent = self.validate_discount(
            percent
        )

        for item in quote.items:

            if item.discount < percent:

                item.discount = percent

        return quote

    # =====================================================
    # Buy X Get Y
    # =====================================================

    def buy_x_get_y(
        self,
        item: QuoteItem,
        buy: int,
        free: int,
    ) -> QuoteItem:

        if buy <= 0 or free <= 0:

            return item

        groups = int(item.quantity // (buy + free))

        free_items = groups * free

        effective_quantity = item.quantity - free_items

        if item.quantity > 0:

            item.discount = (

                (free_items / item.quantity)

                * 100

            )

        return item

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        quote: Quote,
    ) -> dict:

        return {

            "subtotal": quote.subtotal,

            "discount": quote.discount_total,

            "tax": quote.tax_total,

            "grand_total": quote.grand_total,

        }