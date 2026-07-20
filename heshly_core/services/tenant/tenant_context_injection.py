from __future__ import annotations


from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)


class TenantContextInjection:
    """
    Injects tenant context from
    authenticated user.
    """

    def __init__(self):

        self.context = (
            TenantContextManager()
        )


    # =====================================================
    # Inject Tenant
    # =====================================================

    def inject(
        self,
        user: AuthUser,
        tenant: Tenant,
    ):

        if user.tenant_id != tenant.tenant_id:

            raise PermissionError(
                "User does not belong to tenant"
            )


        return self.context.set(
            tenant
        )


    # =====================================================
    # Clear Context
    # =====================================================

    def clear(self):

        self.context.clear()


    # =====================================================
    # Current Tenant
    # =====================================================

    def current(self):

        return self.context.get()


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "tenant_context_injection",

            "status":
                "healthy",

        }