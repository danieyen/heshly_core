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

    subscription_id: str

    tenant_id: str

    business_id: str

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

    grace_period_until: datetime | None = None

    auto_renew: bool = True

    terminated_on: datetime | None = None

    termination_reason: str | None = None

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

    def terminate(
        self,
        reason: str = "Subscription expired",
    ):
        self.status = SubscriptionStatus.EXPIRED
        self.terminated_on = datetime.now(UTC)
        self.termination_reason = reason

    @property
    def is_active(self):
        now = datetime.now(UTC)

        if self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIAL,
        ):
            return True

        if self.status == SubscriptionStatus.PAST_DUE:
            if self.grace_period_until is None:
                return False

            return now < self.grace_period_until

        return False
