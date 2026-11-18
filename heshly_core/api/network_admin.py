"""Admin visibility — pipeline + settings."""

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


def _require_admin():
    try:
        roles = frappe.get_roles() or []
        if "System Manager" not in roles and frappe.session.user != "Administrator":
            frappe.throw("Not permitted", frappe.PermissionError)
    except Exception:
        # allow if frappe not fully booted
        pass


@frappe.whitelist()
def admin_list_network_pipeline(status=None, limit=50, **kwargs):
    _require_admin()
    status = (status or kwargs.get("status") or "").strip() or None
    limit = int(kwargs.get("limit") or limit or 50)
    limit = max(1, min(limit, 200))
    try:
        filters: dict[str, Any] = {}
        if status:
            filters["network_status"] = status
        rows = frappe.get_all("Heshly Network Conversation", filters=filters or None, fields=["*"], order_by="modified desc", limit=limit)
        # attach dispatches summary
        out = []
        for r in rows:
            try:
                dispatches = frappe.get_all("Heshly Network Dispatch", filters={"network_conversation_id": r.get("network_conversation_id")}, fields=["dispatch_id", "tenant_id", "business_id", "status", "attempt_index", "ranking_score", "offered_at", "deadline_at", "responded_at"])
            except Exception:
                dispatches = []
            r["_dispatches"] = dispatches
            out.append(r)
        # counts by status
        counts: dict[str, int] = {}
        try:
            for s in ["NEW", "QUALIFYING", "QUALIFIED", "MATCHED", "OFFERED", "ACCEPTED", "DECLINED", "TIMED_OUT", "REASSIGNED", "COMPLETED", "CANCELLED"]:
                counts[s] = int(frappe.db.count("Heshly Network Conversation", {"network_status": s}) or 0)
        except Exception:
            pass
        return {"success": True, "conversations": out, "counts": counts}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def _serialize_network_conversation(name: str | None = None, network_conversation_id: str | None = None) -> dict | None:
    if not network_conversation_id and not name:
        return None
    try:
        if name and not network_conversation_id:
            doc = frappe.get_doc("Heshly Network Conversation", name)
        elif network_conversation_id:
            doc = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": network_conversation_id.strip()})
        else:
            doc = frappe.get_doc("Heshly Network Conversation", name)  # type: ignore[arg-type]
    except Exception:
        return None
    data: dict[str, Any] = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)  # type: ignore[arg-type]
    # Attach dispatches
    try:
        nid = data.get("network_conversation_id")
        if nid:
            data["_dispatches"] = frappe.get_all(
                "Heshly Network Dispatch",
                filters={"network_conversation_id": nid},
                fields=["dispatch_id", "tenant_id", "business_id", "status", "attempt_index", "ranking_score", "offered_at", "deadline_at", "responded_at"],
                order_by="creation asc",
            )
    except Exception:
        data["_dispatches"] = []
    return data


@frappe.whitelist()
def admin_get_network_conversation(network_conversation_id=None, **kwargs):
    _require_admin()
    nid = (network_conversation_id or kwargs.get("network_conversation_id") or kwargs.get("id") or kwargs.get("name") or "").strip() if isinstance(network_conversation_id or kwargs.get("network_conversation_id") or kwargs.get("id"), str) else (str(network_conversation_id or kwargs.get("network_conversation_id") or kwargs.get("id") or "").strip())
    # handle case where first arg passed as dict via kwargs wrapping
    if not nid:
        # try raw kwargs network_conversation_id
        nid = str(kwargs.get("network_conversation_id") or kwargs.get("id") or kwargs.get("name") or "").strip()
    if not nid:
        return {"success": False, "message": "network_conversation_id is required"}
    data = _serialize_network_conversation(network_conversation_id=nid)
    if not data and frappe.db.exists("Heshly Network Conversation", nid):
        data = _serialize_network_conversation(name=nid)
    if not data:
        return {"success": False, "message": "Network conversation not found"}
    return {"success": True, "conversation": data}


@frappe.whitelist()
def admin_delete_network_conversation(network_conversation_id=None, **kwargs):
    _require_admin()
    nid = str(network_conversation_id or kwargs.get("network_conversation_id") or kwargs.get("id") or kwargs.get("name") or "").strip()
    if not nid:
        return {"success": False, "message": "network_conversation_id is required"}
    # Resolve doc name
    name = None
    if frappe.db.exists("Heshly Network Conversation", nid):
        name = nid
    else:
        name = frappe.db.get_value("Heshly Network Conversation", {"network_conversation_id": nid}, "name")
    if not name:
        return {"success": False, "message": "Network conversation not found"}
    try:
        # Delete related dispatches first (do not cascade automatically)
        nid_val = frappe.db.get_value("Heshly Network Conversation", name, "network_conversation_id")
        try:
            dispatches = frappe.get_all("Heshly Network Conversation Dispatch", filters={"parent": name}, pluck="name")  # child table not dispatch
        except Exception:
            dispatches = []
        # Actually dispatches are separate DocType Heshly Network Dispatch
        try:
            for d in frappe.get_all("Heshly Network Dispatch", filters={"network_conversation_id": nid_val}, pluck="name"):
                frappe.delete_doc("Heshly Network Dispatch", d, ignore_permissions=True)
        except Exception:
            pass
        frappe.delete_doc("Heshly Network Conversation", name, ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Deleted"}
    except Exception as e:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return {"success": False, "message": str(e)}


def admin_get_network_settings(**kwargs):
    _require_admin()
    try:
        doc = frappe.get_single("Heshly Network Settings")
        return {"success": True, "settings": doc.as_dict() if hasattr(doc, "as_dict") else {}}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def admin_update_network_settings(**kwargs):
    _require_admin()
    try:
        doc = frappe.get_single("Heshly Network Settings")
        for k in ["enabled", "central_phone_number", "central_phone_number_id", "central_waba_id", "central_configuration_id", "dispatch_timeout_seconds", "max_dispatch_attempts", "default_lead_fee", "currency", "notify_channel", "central_display_name", "fallback_message"]:
            if k in kwargs and kwargs[k] is not None:
                setattr(doc, k, kwargs[k])
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        try:
            from heshly_core.services.network.settings_service import clear_cache
            clear_cache()
        except Exception:
            pass
        return {"success": True, "message": "Settings updated"}
    except Exception as e:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return {"success": False, "message": str(e)}
