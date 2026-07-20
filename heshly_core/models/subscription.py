from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# =====================================================
# Subscription Status
# =====================================================

class SubscriptionStatus(str, Enum):

    TRIAL = "trial"

    ACTIVE = "active"

    PAST_DUE = "past_due"

    SUSPENDED = "suspended"

    CANCELLED = "cancelled"

    EXPIRED = "expired"


# =====================================================
# Billing Cycle
# =====================================================

class BillingCycle(str, Enum):

    MONTHLY = "monthly"

    QUARTERLY = "quarterly"

    YEARLY = "yearly"


# =====================================================
# Subscription Plan
# =====================================================

@dataclass(slots=True)
class SubscriptionPlan:
    """
    SaaS subscription plan.
    """

    plan_id: str

    name: str

    description: str = ""

    monthly_price: float = 0.0

    yearly_price: float = 0.0

    max_users: int = 1

    max_businesses: int = 1

    max_ai_conversations: int = 0

    max_storage_mb: int = 0

    features: list[str] = field(
        default_factory=list
    )


# =====================================================
# Subscription
# =====================================================

@dataclass(slots=True)
class Subscription:
    """
    Tenant subscription.
    """

    subscription_id: str

    tenant_id: str

    plan: SubscriptionPlan

    status: SubscriptionStatus = (
        SubscriptionStatus.TRIAL
    )

    billing_cycle: BillingCycle = (
        BillingCycle.MONTHLY
    )

    start_date: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    renewal_date: datetime | None = None

    trial_end: datetime | None = None

    cancelled_at: datetime | None = None

    # =================================================
    # Lifecycle
    # =================================================

    def activate(self):

        self.status = SubscriptionStatus.ACTIVE


    def suspend(self):

        self.status = SubscriptionStatus.SUSPENDED


    def cancel(self):

        self.status = SubscriptionStatus.CANCELLED

        self.cancelled_at = datetime.now(UTC)


    def expire(self):

        self.status = SubscriptionStatus.EXPIRED


    @property
    def is_active(self) -> bool:

        return (
            self.status
            in (
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIAL,
            )
        )