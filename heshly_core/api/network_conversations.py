"""Network conversations — tenant sees only where they have a dispatch or are assigned."""

from __future__ import annotations

import json
from typing import Any

try:
    import frappe  # type: ignore
except ImportError:  # pragma: no cover
    class _MockWhitelist:
        def __call__(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator
    class _MockFrappe:
        whitelist = _MockWhitelist()
        request = None
        local = None
    frappe = _MockFrappe()  # type: ignore  # noqa

try:
    from heshly_core.services.tenant.tenant_context import TenantContext
except ImportError:
    TenantContext = None  # type: ignore


def _get_tenant() -> str:
    if TenantContext is None:
        raise ValueError("TenantContext unavailable")
    t = TenantContext().get()
    if not t:
        raise ValueError("tenant_id is required")
    return str(t).strip()


def _is_admin() -> bool:
    try:
        roles = frappe.get_roles() or []
        return "System Manager" in roles or "Administrator" in roles
    except Exception:
        return False


@frappe.whitelist()
def list_network_conversations(status=None, limit=20, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    status = (status or kwargs.get("status") or "").strip() or None
    limit = int(kwargs.get("limit") or limit or 20)
    limit = max(1, min(limit, 100))
    try:
        if _is_admin():
            filters: dict[str, Any] = {}
            if status:
                filters["network_status"] = status
            rows = frappe.get_all("Heshly Network Conversation", filters=filters or None, fields=["*"], order_by="modified desc", limit=limit)
            return {"success": True, "conversations": rows}
        # tenant: only conversations where they have a dispatch or are assigned
        disp_rows = frappe.get_all("Heshly Network Dispatch", filters={"tenant_id": tenant_id}, fields=["network_conversation_id"])
        ids = {r["network_conversation_id"] for r in disp_rows if r.get("network_conversation_id")}
        assigned = frappe.get_all("Heshly Network Conversation", filters={"assigned_tenant_id": tenant_id}, fields=["network_conversation_id"])
        for r in assigned:
            ids.add(r["network_conversation_id"])
        if not ids:
            return {"success": True, "conversations": []}
        flt: dict[str, Any] = {"network_conversation_id": ["in", list(ids)]}
        if status:
            flt["network_status"] = status
        rows = frappe.get_all("Heshly Network Conversation", filters=flt, fields=["*"], order_by="modified desc", limit=limit)
        return {"success": True, "conversations": rows}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_network_conversation(network_conversation_id=None, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    nid = network_conversation_id or kwargs.get("network_conversation_id") or kwargs.get("id")
    if not nid:
        return {"success": False, "message": "network_conversation_id is required"}
    try:
        doc = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": str(nid).strip()})
        if not doc:
            return {"success": False, "message": "Not found"}
        # authz: admin or has dispatch or assigned
        if not _is_admin():
            has_dispatch = bool(frappe.db.exists("Heshly Network Dispatch", {"network_conversation_id": str(nid).strip(), "tenant_id": tenant_id}))
            is_assigned = str(getattr(doc, "assigned_tenant_id", "") or "") == tenant_id
            if not (has_dispatch or is_assigned):
                return {"success": False, "message": "Not authorized"}
        # serialize
        data = doc.as_dict() if hasattr(doc, "as_dict") else {}
        # privacy: hide customer phone until assigned (show masked) unless assigned
        is_assigned = str(getattr(doc, "assigned_tenant_id", "") or "") == tenant_id or _is_admin()
        if not is_assigned:
            phone = data.get("customer_phone") or ""
            if phone and len(phone) > 4:
                data["customer_phone_masked"] = phone[:3] + "****" + phone[-4:]
                # keep original for assigned view via dispatch; for list hide it
        return {"success": True, "conversation": data}
    except Exception as e:
        return {"success": False, "message": str(e)}
