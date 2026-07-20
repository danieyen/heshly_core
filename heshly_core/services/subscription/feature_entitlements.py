from __future__ import annotations

from heshly_core.models.subscription import (
    SubscriptionPlan,
)


class FeatureEntitlements:
    """
    Feature entitlement service.

    Determines whether a subscription
    plan includes a specific feature.
    """

    # =====================================================
    # Features
    # =====================================================

    @staticmethod
    def has_feature(
        plan: SubscriptionPlan,
        feature: str,
    ) -> bool:

        return feature in plan.features

    @staticmethod
    def require_feature(
        plan: SubscriptionPlan,
        feature: str,
    ) -> None:

        if not FeatureEntitlements.has_feature(
            plan,
            feature,
        ):
            raise PermissionError(
                f"Feature '{feature}' is not included in the '{plan.name}' plan."
            )

    @staticmethod
    def features(
        plan: SubscriptionPlan,
    ) -> list[str]:

        return list(plan.features)

    @staticmethod
    def feature_count(
        plan: SubscriptionPlan,
    ) -> int:

        return len(plan.features)

    @staticmethod
    def summary(
        plan: SubscriptionPlan,
    ) -> dict:

        return {
            "plan": plan.name,
            "features": FeatureEntitlements.feature_count(plan),
            "available": FeatureEntitlements.features(plan),
        }

    @staticmethod
    def health() -> dict:

        return {
            "service": "feature_entitlements",
            "status": "healthy",
        }