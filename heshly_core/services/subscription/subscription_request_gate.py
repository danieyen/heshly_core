from __future__ import annotations

from heshly_core.services.subscription.subscription_access import (
    SubscriptionAccess,
)
from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class SubscriptionRequestGate:
    """
    Enforces subscription entitlement after tenant resolution.

    TenantContext establishes the canonical tenant.
    SubscriptionAccess determines whether that tenant's
    business subscription permits access.
    """

    def __init__(
        self,
        access: SubscriptionAccess | None = None,
    ):
        self.access = (
            access
            or SubscriptionAccess()
        )

        self.context = TenantContext()

    def require_access(
        self,
        business_id: str,
    ) -> None:

        self.context.require()

        self.access.require_access(
            business_id
    )

    def health(self) -> dict:

        return {
            "service": "subscription_request_gate",
            "status": "healthy",
            "tenant": self.context.get(),
            "has_context": self.context.has_context(),
        }
