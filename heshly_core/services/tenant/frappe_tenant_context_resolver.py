from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


class FrappeTenantContextResolver:
    """
    Resolves the canonical tenant_id from the authenticated
    Frappe user and their active business membership.

    Resolution chain:

        frappe.session.user
            ↓
        User Business Membership
            ↓
        tenant_id
            ↓
        TenantContext
    """

    def __init__(self):
        self.context = TenantContext()

    def resolve(self, business_id: str) -> str:
        user = frappe.session.user

        if not user or user == "Guest":
            raise PermissionError(
                "Authenticated user required for tenant resolution."
            )

        if not business_id:
            raise ValueError(
                "business_id is required for tenant resolution."
            )

        membership = frappe.db.get_value(
            "User Business Membership",
            {
                "user": user,
                "business_id": business_id,
                "active": 1,
            },
            [
                "tenant_id",
                "business_id",
                "role",
            ],
            as_dict=True,
        )

        if not membership:
            raise PermissionError(
                f"User '{user}' has no active membership "
                f"for business '{business_id}'."
            )

        tenant_id = membership.get("tenant_id")

        if not tenant_id:
            raise ValueError(
                f"Active membership for user '{user}' "
                f"and business '{business_id}' has no tenant_id."
            )

        self.context.set(tenant_id)

        return tenant_id

    def current(self) -> str:
        return self.context.require()

    def clear(self) -> None:
        self.context.clear()

    def health(self):
        return {
            "service": "frappe_tenant_context_resolver",
            "status": "healthy",
            "user": frappe.session.user,
            "context": self.context.has_context(),
        }
