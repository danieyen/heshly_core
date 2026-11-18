"""Network document permissions — additive."""

from __future__ import annotations

from typing import Any

import frappe  # type: ignore

from heshly_core.services.tenant.tenant_context import TenantContext


def _is_admin(user: str | None) -> bool:
    try:
        roles = frappe.get_roles(user) or frappe.get_roles() or []  # type: ignore
        if "System Manager" in roles:
            return True
        if (user or frappe.session.user) == "Administrator":
            return True
    except Exception:
        pass
    return False


def heshly_network_membership_has_permission(doc: Any, ptype: str | None = None, user: str | None = None, debug: bool = False) -> bool:
    if _is_admin(user):
        return True
    if ptype == "create":
        return bool(TenantContext().get())
    tenant_id = TenantContext().get()
    return bool(tenant_id and getattr(doc, "tenant_id", None) == tenant_id)


def heshly_network_dispatch_has_permission(doc: Any, ptype: str | None = None, user: str | None = None, debug: bool = False) -> bool:
    if _is_admin(user):
        return True
    if ptype == "create":
        return True  # created via system with ignore_permissions; ptype checks still gated at API
    tenant_id = TenantContext().get()
    return bool(tenant_id and getattr(doc, "tenant_id", None) == tenant_id)


def heshly_network_conversation_has_permission(doc: Any, ptype: str | None = None, user: str | None = None, debug: bool = False) -> bool:
    if _is_admin(user):
        return True
    if ptype == "create":
        return True  # system creates with ignore_permissions
    tenant_id = TenantContext().get()
    if not tenant_id:
        return False
    # allow if tenant has a dispatch for this conversation or is assigned
    try:
        if getattr(doc, "assigned_tenant_id", None) == tenant_id:
            return True
        nid = getattr(doc, "network_conversation_id", None)
        if nid and frappe.db.exists("Heshly Network Dispatch", {"network_conversation_id": nid, "tenant_id": tenant_id}):
            return True
    except Exception:
        pass
    return False
