from __future__ import annotations

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionPlan,
)


class UpgradeDowngradeFlow:
    """
    Upgrade / Downgrade Flow.

    Handles subscription plan changes.

    Future:
        • Prorated billing
        • Scheduled plan changes
        • Payment validation
        • Usage limit checks
        • Billing provider integration
    """

    # =====================================================
    # Plan Changes
    # =====================================================

    def change_plan(
        self,
        subscription: Subscription,
        new_plan: SubscriptionPlan,
    ) -> Subscription:

        if subscription.plan.plan_id == new_plan.plan_id:
            return subscription

        subscription.plan = new_plan

        return subscription

    def upgrade(
        self,
        subscription: Subscription,
        new_plan: SubscriptionPlan,
    ) -> Subscription:

        return self.change_plan(
            subscription,
            new_plan,
        )

    def downgrade(
        self,
        subscription: Subscription,
        new_plan: SubscriptionPlan,
    ) -> Subscription:

        return self.change_plan(
            subscription,
            new_plan,
        )

    # =====================================================
    # Helpers
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
        }

    def health(self) -> dict:

        return {
            "service": "upgrade_downgrade_flow",
            "status": "healthy",
        }