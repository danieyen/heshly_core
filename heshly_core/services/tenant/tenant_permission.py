from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


class TenantPermission:
    """
    Prevents cross-tenant access.

    TenantContext is the single canonical source of
    the current tenant_id.
    """

    def __init__(self):
        self.context = TenantContext()

    # =====================================================
    # Current Tenant
    # =====================================================

    def current_tenant(self) -> str:

        return self.context.require()

    # =====================================================
    # Check document ownership
    # =====================================================

    def can_access(
        self,
        doc,
    ) -> bool:

        tenant_id = self.current_tenant()

        return (
            getattr(
                doc,
                "tenant_id",
                None,
            )
            == tenant_id
        )

    # =====================================================
    # Require access
    # =====================================================

    def require_access(
        self,
        doc,
    ) -> None:

        if not self.can_access(doc):

            frappe.throw(
                "Cross tenant access denied",
                frappe.PermissionError,
            )

    # =====================================================
    # Database filter
    # =====================================================

    def tenant_filter(
        self,
    ) -> dict:

        return {
            "tenant_id": self.current_tenant()
        }

    # =====================================================
    # Health
    # =====================================================

    def health(
        self,
    ) -> dict:

        return {
            "service": "tenant_permission",
            "status": "healthy",
            "tenant": self.context.get(),
            "has_context": self.context.has_context(),
        }
