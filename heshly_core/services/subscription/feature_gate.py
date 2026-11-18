from __future__ import annotations

from heshly_core.services.subscription.business_subscription_service import (
    BusinessSubscriptionService,
)

from heshly_core.services.subscription.feature_entitlements import (
    FeatureEntitlements,
)


class FeatureGate:
    """
    SaaS Feature Access Gate.

    Determines whether a business has access
    to a particular feature based on its
    active subscription.
    """

    def __init__(
        self,
        subscription_service: BusinessSubscriptionService | None = None,
    ):

        self.subscription_service = (
            subscription_service
            or BusinessSubscriptionService()
        )

    # =====================================================
    # Feature Check
    # =====================================================

    def can_use(
        self,
        business_id: str,
        feature: str,
    ) -> bool:

        subscription = (
            self.subscription_service.get_subscription(
                business_id
            )
        )

        if subscription is None:
            return False

        return FeatureEntitlements.has_feature(
            subscription.plan,
            feature,
        )

    # =====================================================
    # Require Feature
    # =====================================================

    def require(
        self,
        business_id: str,
        feature: str,
    ) -> None:

        if not self.can_use(
            business_id,
            feature,
        ):
            raise PermissionError(
                f"Business '{business_id}' does not have access to '{feature}'"
            )

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        business_id: str,
    ) -> dict:

        subscription = (
            self.subscription_service.get_subscription(
                business_id
            )
        )

        if subscription is None:
            return {
                "business_id": business_id,
                "subscription": None,
                "features": [],
            }

        return {
            "business_id": business_id,
            "subscription_id": subscription.subscription_id,
            "plan": subscription.plan.name,
            "status": subscription.status.value,
            "features": subscription.plan.features,
        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {
            "service": "feature_gate",
            "status": "healthy",
        }
