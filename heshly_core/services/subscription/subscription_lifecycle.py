from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)


class SubscriptionLifecycle:
    """
    Subscription Lifecycle.

    Coordinates subscription state
    transitions.

    Future:
        • Automatic renewals
        • Payment webhooks
        • Grace periods
        • Trial expiration
        • Billing retries
    """

    # =====================================================
    # Lifecycle
    # =====================================================

    def activate(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.activate()

        return subscription


    def suspend(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.suspend()

        return subscription


    def cancel(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.cancel()

        return subscription


    def expire(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.expire()

        return subscription


    def mark_past_due(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.status = (
            SubscriptionStatus.PAST_DUE
        )

        return subscription


    def renew(
        self,
        subscription: Subscription,
        renewal_date: datetime,
    ) -> Subscription:

        subscription.status = (
            SubscriptionStatus.ACTIVE
        )

        subscription.renewal_date = renewal_date

        return subscription

    # =====================================================
    # Validation
    # =====================================================

    def can_access(
        self,
        subscription: Subscription,
    ) -> bool:

        return subscription.is_active

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        subscription: Subscription,
    ) -> dict:

        return {
            "subscription_id": subscription.subscription_id,
            "tenant_id": subscription.tenant_id,
            "plan": subscription.plan.name,
            "status": subscription.status.value,
            "active": subscription.is_active,
        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {
            "service": "subscription_lifecycle",
            "status": "healthy",
        }