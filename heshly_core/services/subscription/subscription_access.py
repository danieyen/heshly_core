from __future__ import annotations

from datetime import datetime

from heshly_core.repositories.frappe_subscription_repository import (
    FrappeSubscriptionRepository,
)
from heshly_core.services.subscription.subscription_lifecycle import (
    SubscriptionLifecycle,
)


class SubscriptionAccess:
    """
    Determines whether a business is entitled to use Heshly.

    TenantContext establishes the security boundary.
    The business_id identifies the business within that tenant.
    SubscriptionLifecycle determines the current subscription state.
    """

    def __init__(
        self,
        repository: FrappeSubscriptionRepository | None = None,
        lifecycle: SubscriptionLifecycle | None = None,
    ):
        self.repository = (
            repository
            or FrappeSubscriptionRepository()
        )

        self.lifecycle = (
            lifecycle
            or SubscriptionLifecycle()
        )

    # =====================================================
    # Subscription
    # =====================================================

    def get_subscription(
        self,
        business_id: str,
    ):
        """
        Return the current subscription belonging to the
        business in the current tenant.
        """

        return self.repository.get_by_business(
            business_id
        )

    # =====================================================
    # Evaluate
    # =====================================================

    def evaluate(
        self,
        business_id: str,
        now: datetime | None = None,
    ):
        """
        Evaluate the subscription lifecycle before
        determining access.
        """

        subscription = self.get_subscription(
            business_id
        )

        if subscription is None:
            return None

        self.lifecycle.evaluate(
            subscription,
            now=now,
        )

        return subscription

    # =====================================================
    # Access
    # =====================================================

    def can_access(
        self,
        business_id: str,
        now: datetime | None = None,
    ) -> bool:

        subscription = self.evaluate(
            business_id,
            now=now,
        )

        if subscription is None:
            return False

        return subscription.is_active

    # =====================================================
    # Require Access
    # =====================================================

    def require_access(
        self,
        business_id: str,
        now: datetime | None = None,
    ) -> None:

        subscription = self.evaluate(
            business_id,
            now=now,
        )

        if subscription is None:
            raise PermissionError(
                "No active Heshly subscription."
            )

        if not subscription.is_active:
            raise PermissionError(
                "Heshly subscription is not active."
            )

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {
            "service": "subscription_access",
            "status": "healthy",
        }