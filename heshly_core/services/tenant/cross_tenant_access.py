from __future__ import annotations

from typing import Any

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)


class CrossTenantAccess:
    """
    Cross-Tenant Access Prevention.

    Prevents one tenant from accessing
    another tenant's resources.
    """

    def __init__(self):

        self.context = TenantContextManager()

    # =====================================================
    # Authorization
    # =====================================================

    def authorize(
        self,
        resource: Any,
    ) -> bool:

        tenant = self.context.require()

        resource_tenant = getattr(
            resource,
            "tenant_id",
            None,
        )

        if resource_tenant != tenant.tenant_id:

            raise PermissionError(
                "Cross-tenant access denied."
            )

        return True

    # =====================================================
    # Safe Access
    # =====================================================

    def can_access(
        self,
        resource: Any,
    ) -> bool:

        tenant = self.context.get()

        if tenant is None:

            return False

        return (

            getattr(
                resource,
                "tenant_id",
                None,
            )

            ==

            tenant.tenant_id

        )

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "service": "cross_tenant_access",

            "status": "healthy",

        }