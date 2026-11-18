from __future__ import annotations

from heshly_core.models.subscription import Subscription

from heshly_core.repositories.frappe_subscription_repository import (
    FrappeSubscriptionRepository,
)


class BusinessSubscriptionService:
    """
    Business -> Subscription lookup service.

    Single place that knows how to retrieve
    a subscription for a business.
    """

    def __init__(
        self,
        repository: FrappeSubscriptionRepository | None = None,
    ):

        self.repository = (
            repository
            or FrappeSubscriptionRepository()
        )

    # =====================================================
    # Get Subscription
    # =====================================================

    def get_subscription(
        self,
        business_id: str,
    ) -> Subscription | None:

        return self.repository.get_by_business(
            business_id
        )

    # =====================================================
    # Has Subscription
    # =====================================================

    def has_subscription(
        self,
        business_id: str,
    ) -> bool:

        return (
            self.get_subscription(
                business_id
            )
            is not None
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "business_subscription_service",

            "status": "healthy",

        }
