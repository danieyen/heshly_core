"""Network permission query conditions — additive."""

from __future__ import annotations

import frappe  # type: ignore

from heshly_core.services.tenant.tenant_context import TenantContext


def _tenant_condition() -> str:
    tenant_id = TenantContext().get()
    if not tenant_id:
        return "1 = 0"
    return "tenant_id = " + frappe.db.escape(tenant_id)


def heshly_network_membership_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_network_dispatch_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_network_conversation_query(user: str | None = None) -> str:
    # Network conversations are owned by HESHLY NETWORK, not a tenant.
    # Row-level isolation is enforced in the API layer (dispatch/assigned check).
    # For System Manager, allow all; otherwise allow nothing at DB filter level
    # and let API handle tenant-visible subset via explicit queries.
    try:
        roles = frappe.get_roles(user) or []  # type: ignore
        if "System Manager" in roles or user == "Administrator":
            return "1 = 1"
    except Exception:
        pass
    # Non-admins access via API that does explicit dispatch-based filtering,
    # so PQC should allow 1=1 for doc fetch but API checks authz.
    # We return 1=1 and enforce in document_permissions instead.
    return "1 = 1"
