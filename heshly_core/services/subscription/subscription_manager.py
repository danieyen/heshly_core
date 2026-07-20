from __future__ import annotations

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionPlan,
)

from heshly_core.services.subscription.feature_entitlements import (
    FeatureEntitlements,
)


class SubscriptionManager:
    """
    Subscription Manager.

    Central service responsible for
    managing SaaS subscriptions.

    Future:
        • Billing integration
        • Stripe
        • M-Pesa
        • PayPal
        • Automatic renewals
    """

    def __init__(self):

        self._subscriptions: dict[
            str,
            Subscription,
        ] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def create(
        self,
        subscription: Subscription,
    ) -> Subscription:

        self._subscriptions[
            subscription.subscription_id
        ] = subscription

        return subscription

    def get(
        self,
        subscription_id: str,
    ) -> Subscription | None:

        return self._subscriptions.get(
            subscription_id
        )

    def all(
        self,
    ) -> list[Subscription]:

        return list(
            self._subscriptions.values()
        )

    def delete(
        self,
        subscription_id: str,
    ) -> None:

        self._subscriptions.pop(
            subscription_id,
            None,
        )

    # =====================================================
    # Lifecycle
    # =====================================================

    def activate(
        self,
        subscription_id: str,
    ) -> Subscription:

        subscription = self.require(
            subscription_id,
        )

        subscription.activate()

        return subscription

    def suspend(
        self,
        subscription_id: str,
    ) -> Subscription:

        subscription = self.require(
            subscription_id,
        )

        subscription.suspend()

        return subscription

    def cancel(
        self,
        subscription_id: str,
    ) -> Subscription:

        subscription = self.require(
            subscription_id,
        )

        subscription.cancel()

        return subscription

    # =====================================================
    # Plans
    # =====================================================

    def change_plan(
        self,
        subscription_id: str,
        plan: SubscriptionPlan,
    ) -> Subscription:

        subscription = self.require(
            subscription_id,
        )

        subscription.plan = plan

        return subscription

    # =====================================================
    # Features
    # =====================================================

    def has_feature(
        self,
        subscription_id: str,
        feature: str,
    ) -> bool:

        subscription = self.require(
            subscription_id,
        )

        return FeatureEntitlements.has_feature(
            subscription.plan,
            feature,
        )

    # =====================================================
    # Helpers
    # =====================================================

    def require(
        self,
        subscription_id: str,
    ) -> Subscription:

        subscription = self.get(
            subscription_id,
        )

        if subscription is None:
            raise ValueError(
                f"Subscription '{subscription_id}' not found."
            )

        return subscription

    def clear(self):

        self._subscriptions.clear()

    def summary(self) -> dict:

        return {
            "subscriptions": len(
                self._subscriptions
            ),
            "active": sum(
                1
                for subscription
                in self._subscriptions.values()
                if subscription.is_active
            ),
        }

    def health(self) -> dict:

        return {
            "service": "subscription_manager",
            "status": "healthy",
        }