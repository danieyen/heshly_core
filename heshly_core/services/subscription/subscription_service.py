from __future__ import annotations

from datetime import datetime

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)

from heshly_core.repositories.frappe_subscription_repository import (
    FrappeSubscriptionRepository,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.subscription.subscription_state_machine import (
    SubscriptionStateMachine,
)


class SubscriptionService:

    def __init__(
        self,
        repository: FrappeSubscriptionRepository | None = None,
        tenant_context: TenantContext | None = None,
    ):
        self.repository = (
            repository
            or FrappeSubscriptionRepository()
        )

        self.tenant_context = (
            tenant_context
            or TenantContext()
        )


    def create_subscription(
        self,
        subscription_id: str,
        business_id: str,
        plan: SubscriptionPlan,
    ) -> Subscription:

        tenant_id = self.tenant_context.get()

        if not tenant_id:
            raise RuntimeError(
                "No active tenant context."
            )

        subscription = Subscription(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            business_id=business_id,
            plan=plan,
            status=SubscriptionStatus.TRIAL,
        )

        return self.repository.save(
            subscription
        )


    def get_subscription(
        self,
        business_id: str,
    ) -> Subscription | None:

        return self.repository.get_by_business(
            business_id
        )


    def get_latest_subscription(
        self,
        business_id: str,
    ) -> Subscription | None:

        return self.repository.get_any_by_business(
            business_id
        )



    def activate_subscription(
        self,
        business_id: str,
    ) -> Subscription:

        subscription = self.get_latest_subscription(
            business_id
        )

        if not subscription:
            raise ValueError(
                "No subscription found."
            )

        SubscriptionStateMachine.validate(
            subscription.status,
            SubscriptionStatus.ACTIVE,
        )

        subscription.status = (
            SubscriptionStatus.ACTIVE
        )

        return self.repository.save(
            subscription
        )


    def cancel_subscription(
        self,
        business_id: str,
        reason: str | None = None,
    ) -> Subscription:

        subscription = self.get_subscription(
            business_id
        )

        if not subscription:
            raise ValueError(
                "No subscription found."
            )

        SubscriptionStateMachine.validate(
            subscription.status,
            SubscriptionStatus.CANCELLED,
        )

        subscription.status = (
            SubscriptionStatus.CANCELLED
        )

        subscription.cancelled_at = datetime.utcnow()

        return self.repository.save(
            subscription
        )
