from __future__ import annotations

from heshly_core.models.subscription import (
    Subscription,
)


class SubscriptionRepository:
    """
    Shared in-memory Subscription Repository.

    Future:
    ERPNext / Database persistence.
    """

    _subscriptions: dict[str, Subscription] = {}


    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        subscription: Subscription,
    ) -> Subscription:

        self._subscriptions[
            subscription.subscription_id
        ] = subscription

        return subscription


    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        subscription_id: str,
    ) -> Subscription | None:

        return self._subscriptions.get(
            subscription_id
        )


    # =====================================================
    # Get By Business
    # =====================================================

    def get_by_business(
        self,
        business_id: str,
    ) -> Subscription | None:

        for subscription in self._subscriptions.values():

            if subscription.business_id == business_id:

                return subscription

        return None


    # =====================================================
    # All
    # =====================================================

    def all(self):

        return list(
            self._subscriptions.values()
        )


    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        subscription_id: str,
    ):

        self._subscriptions.pop(
            subscription_id,
            None,
        )


    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._subscriptions.clear()


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "repository": "subscription_repository",

            "status": "healthy",

            "records": len(
                self._subscriptions
            ),

        }
