from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from heshly_core.models.payment import (
    PaymentMethod,
    PaymentRequest,
    PaymentResult,
    RefundRequest,
    RefundResult,
)


class PaymentProviderType(str, Enum):
    ERPNEXT = "erpnext"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MPESA = "mpesa"


@dataclass(slots=True)
class ProviderConfiguration:
    """
    Configuration for a payment provider.
    """

    provider: PaymentProviderType

    enabled: bool = True

    sandbox: bool = True

    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderCapabilities:
    """
    Features supported by a payment provider.
    """

    supports_refunds: bool = False

    supports_partial_payments: bool = False

    supports_payment_links: bool = True

    supports_webhooks: bool = True

    supports_recurring_payments: bool = False


@dataclass(slots=True)
class ProviderPaymentRequest:
    """
    Internal request sent to a provider.
    """

    payment: PaymentRequest

    configuration: ProviderConfiguration


@dataclass(slots=True)
class ProviderPaymentResult:
    """
    Provider payment response.
    """

    result: PaymentResult

    provider: PaymentProviderType

    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderRefundRequest:
    """
    Internal refund request.
    """

    refund: RefundRequest

    configuration: ProviderConfiguration


@dataclass(slots=True)
class ProviderRefundResult:
    """
    Provider refund response.
    """

    result: RefundResult

    provider: PaymentProviderType

    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderInfo:
    """
    Information describing a payment provider.
    """

    provider: PaymentProviderType

    name: str

    payment_method: PaymentMethod

    capabilities: ProviderCapabilities