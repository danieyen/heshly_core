from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class Currency(str, Enum):
    KES = "KES"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class PaymentStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MPESA = "mpesa"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    OTHER = "other"


@dataclass(slots=True)
class PaymentItem:
    description: str
    quantity: Decimal
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass(slots=True)
class Quote:
    quote_id: str
    customer_id: str
    currency: Currency

    items: list[PaymentItem] = field(default_factory=list)

    expires_at: datetime | None = None
    notes: str | None = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total(self) -> Decimal:
        return sum(
            (item.total for item in self.items),
            start=Decimal("0"),
        )


@dataclass(slots=True)
class Invoice:
    invoice_id: str
    customer_id: str
    currency: Currency

    items: list[PaymentItem] = field(default_factory=list)

    status: PaymentStatus = PaymentStatus.DRAFT

    quote_id: str | None = None

    due_date: datetime | None = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total(self) -> Decimal:
        return sum(
            (item.total for item in self.items),
            start=Decimal("0"),
        )


@dataclass(slots=True)
class PaymentRequest:
    invoice_id: str
    amount: Decimal
    currency: Currency
    method: PaymentMethod

    callback_url: str | None = None
    reference: str | None = None

    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class PaymentResult:
    success: bool
    status: PaymentStatus

    transaction_id: str | None = None

    provider_reference: str | None = None

    payment_url: str | None = None

    paid_at: datetime | None = None

    message: str | None = None

    raw_response: dict = field(default_factory=dict)


@dataclass(slots=True)
class RefundRequest:
    transaction_id: str
    amount: Decimal
    reason: str


@dataclass(slots=True)
class RefundResult:
    success: bool

    refund_id: str | None = None

    status: PaymentStatus | None = None

    message: str | None = None