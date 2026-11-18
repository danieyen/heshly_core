from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProvider(Enum):
    STRIPE = "stripe"
    MPESA = "mpesa"
    PAYPAL = "paypal"


@dataclass
class Payment:

    payment_id: str

    tenant_id: str
    business_id: str

    subscription_id: str

    provider: PaymentProvider

    amount: float
    currency: str = "USD"

    status: PaymentStatus = PaymentStatus.PENDING

    provider_reference: str | None = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

    completed_at: datetime | None = None
