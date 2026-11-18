from __future__ import annotations

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionPlan,
)

from heshly_core.repositories.frappe_subscription_repository import (
    FrappeSubscriptionRepository,
)

from heshly_core.services.subscription.feature_entitlements import (
    FeatureEntitlements,
)


class SubscriptionManager:
    """
    Subscription Manager.

    Central service responsible for managing
    Heshly SaaS subscriptions.
    """

    def __init__(self):

        self.repository = (
            FrappeSubscriptionRepository()
        )

    # =====================================================
    # CRUD
    # =====================================================

    def create(
        self,
        subscription: Subscription,
    ) -> Subscription:

        return self.repository.save(
            subscription
        )

    def get(
        self,
        subscription_id: str,
    ) -> Subscription | None:

        return self.repository.get(
            subscription_id
        )

    def get_by_business(
        self,
        business_id: str,
    ) -> Subscription | None:

        return self.repository.get_by_business(
            business_id
        )

    def all(
        self,
    ) -> list[Subscription]:

        return self.repository.all()

    def delete(
        self,
        subscription_id: str,
    ) -> None:

        self.repository.delete(
            subscription_id
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

        self.repository.save(
            subscription,
        )

        return subscription

    def suspend(
        self,
        subscription_id: str,
    ) -> Subscription:

        subscription = self.require(
            subscription_id,
        )

        subscription.suspend()

        self.repository.save(
            subscription,
        )

        return subscription

    def cancel(
        self,
        subscription_id: str,
    ) -> Subscription:

        subscription = self.require(
            subscription_id,
        )

        subscription.cancel()

        self.repository.save(
            subscription,
        )

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

        self.repository.save(
            subscription,
        )

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

    def clear(
        self,
    ):

        self.repository.clear()

    def summary(
        self,
    ) -> dict:

        subscriptions = self.repository.all()

        return {

            "subscriptions": len(
                subscriptions
            ),

            "active": sum(
                1
                for subscription in subscriptions
                if subscription.is_active
            ),
        }

    def health(
        self,
    ) -> dict:

        return {

            "service": "subscription_manager",

            "status": "healthy",

            "repository": "frappe",
        }
