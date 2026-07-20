from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, UTC
from enum import Enum
from typing import Optional


# ==========================================================
# ENUMS
# ==========================================================

class QuoteStatus(str, Enum):

    DRAFT = "draft"

    SENT = "sent"

    ACCEPTED = "accepted"

    REJECTED = "rejected"

    EXPIRED = "expired"

    CANCELLED = "cancelled"


class QuoteItemType(str, Enum):

    SERVICE = "service"

    PRODUCT = "product"

    DISCOUNT = "discount"

    OTHER = "other"


# ==========================================================
# QUOTE ITEM
# ==========================================================

@dataclass(slots=True)
class QuoteItem:

    item_id: str

    item_type: QuoteItemType

    name: str

    description: Optional[str] = None

    quantity: float = 1.0

    unit_price: float = 0.0

    discount: float = 0.0

    tax_rate: float = 0.0

    @property
    def subtotal(self) -> float:

        return self.quantity * self.unit_price

    @property
    def discount_amount(self) -> float:

        return self.subtotal * (self.discount / 100)

    @property
    def taxable_amount(self) -> float:

        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self) -> float:

        return self.taxable_amount * (
            self.tax_rate / 100
        )

    @property
    def total(self) -> float:

        return self.taxable_amount + self.tax_amount


# ==========================================================
# QUOTE
# ==========================================================

@dataclass(slots=True)
class Quote:

    quote_id: str

    business_id: str

    customer_id: str

    opportunity_id: Optional[str] = None

    quote_number: str = ""

    title: str = ""

    currency: str = "KES"

    status: QuoteStatus = QuoteStatus.DRAFT

    issue_date: date = field(
        default_factory=date.today
    )

    expiry_date: Optional[date] = None

    items: list[QuoteItem] = field(
        default_factory=list
    )

    notes: Optional[str] = None

    terms: Optional[str] = None

    created_by: Optional[str] = None

    approved_by: Optional[str] = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    # ======================================================
    # CALCULATED VALUES
    # ======================================================

    @property
    def subtotal(self) -> float:

        return round(

            sum(
                item.subtotal
                for item in self.items
            ),

            2,

        )

    @property
    def discount_total(self) -> float:

        return round(

            sum(
                item.discount_amount
                for item in self.items
            ),

            2,

        )

    @property
    def taxable_total(self) -> float:

        return round(

            sum(
                item.taxable_amount
                for item in self.items
            ),

            2,

        )

    @property
    def tax_total(self) -> float:

        return round(

            sum(
                item.tax_amount
                for item in self.items
            ),

            2,

        )

    @property
    def grand_total(self) -> float:

        return round(

            sum(
                item.total
                for item in self.items
            ),

            2,

        )

    @property
    def total_items(self) -> int:

        return len(self.items)

    @property
    def is_expired(self) -> bool:

        if self.expiry_date is None:

            return False

        return self.expiry_date < date.today()

    # ======================================================
    # OPERATIONS
    # ======================================================

    def add_item(
        self,
        item: QuoteItem,
    ) -> None:

        self.items.append(item)

        self.updated_at = datetime.now(UTC)

    def remove_item(
        self,
        item_id: str,
    ) -> bool:

        for index, item in enumerate(self.items):

            if item.item_id == item_id:

                del self.items[index]

                self.updated_at = datetime.now(UTC)

                return True

        return False