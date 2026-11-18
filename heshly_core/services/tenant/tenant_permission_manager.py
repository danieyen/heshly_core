from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


class TenantPermissionManager:
    """
    Central tenant authorization service.

    business_id and tenant_id are different concepts.

    This class operates on tenant_id because TenantContext
    stores the canonical tenant identifier.
    """

    SYSTEM_USERS = {
        "Administrator",
    }

    def __init__(self):
        self.context = TenantContext()

    def current_tenant(self) -> str:
        return self.context.require()

    def is_system_admin(self) -> bool:
        return frappe.session.user in self.SYSTEM_USERS

    def can_access_tenant(self, tenant_id: str) -> bool:
        if self.is_system_admin():
            return True

        try:
            current = self.current_tenant()
        except RuntimeError:
            return False

        return current == tenant_id

    def require_tenant(self, tenant_id: str) -> None:
        if not self.can_access_tenant(tenant_id):
            raise PermissionError(
                f"Access denied to tenant '{tenant_id}'."
            )

    def require_current_tenant(self, tenant_id: str) -> str:
        self.require_tenant(tenant_id)
        return tenant_id

    def require_context(self) -> str:
        return self.context.require()

    def health(self):
        return {
            "service": "tenant_permission_manager",
            "status": "healthy",
            "system_admin": self.is_system_admin(),
        }
