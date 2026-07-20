from __future__ import annotations

from contextvars import ContextVar

from heshly_core.models.tenant import (
    Tenant,
)


class TenantContextManager:
    """
    Shared Tenant Context Manager.

    Maintains the active tenant context
    across Heshly services.

    Used by:

    - API requests
    - AI engine
    - CRM
    - Calendar
    - Analytics
    """


    _tenant_context = ContextVar(
        "tenant_context",
        default=None,
    )


    # =====================================================
    # Set Tenant
    # =====================================================

    def set(
        self,
        tenant: Tenant,
    ):

        return self._tenant_context.set(
            tenant
        )


    # =====================================================
    # Get Tenant
    # =====================================================

    def get(self) -> Tenant | None:

        return self._tenant_context.get()


    # =====================================================
    # Require Tenant
    # =====================================================

    def require(self) -> Tenant:

        tenant = self.get()


        if tenant is None:

            raise RuntimeError(
                "No tenant context available"
            )


        return tenant


    # =====================================================
    # Tenant ID
    # =====================================================

    def tenant_id(self) -> str | None:

        tenant = self.get()


        if tenant is None:

            return None


        return tenant.tenant_id


    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._tenant_context.set(
            None
        )


    # =====================================================
    # Exists
    # =====================================================

    def has_context(self) -> bool:

        return self.get() is not None


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_context_manager",

            "status": "healthy",

            "tenant_id": self.tenant_id(),

        }