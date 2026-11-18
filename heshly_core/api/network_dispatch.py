"""Network dispatch APIs — tenant sees only own dispatches."""

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


def _parse_json_if_string(v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        if s and ((s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]"))):
            try:
                return json.loads(s)
            except Exception:
                return v
    return v


def _unwrap(payload: Any, kwargs: dict) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(kwargs, dict):
        # keep explicit dispatch_id etc
        for k, v in kwargs.items():
            if k not in ("payload",):
                data[k] = v
    if payload is not None:
        parsed = _parse_json_if_string(payload)
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if k not in data:
                    data[k] = v
    for _ in range(3):
        wrapped = None
        for key in ("$json", "json", "body", "data"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_if_string(data[key])
                if isinstance(val, dict):
                    wrapped = val
                    break
        if wrapped is not None:
            merged = dict(data)
            for k in ("$json", "json", "body", "data"):
                merged.pop(k, None)
            for k, v in wrapped.items():
                if k not in merged or merged[k] in (None, ""):
                    merged[k] = v
            data = merged
        else:
            break
    return data


@frappe.whitelist()
def list_my_dispatches(payload=None, status=None, limit=50, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    data = _unwrap(payload, kwargs)
    status = status or data.get("status")
    limit = int(data.get("limit") or limit or 50)
    limit = max(1, min(limit, 100))
    try:
        filters: dict[str, Any] = {"tenant_id": tenant_id}
        if status and str(status).strip():
            filters["status"] = str(status).strip()
        rows = frappe.get_all("Heshly Network Dispatch", filters=filters, fields=["*"], order_by="offered_at desc", limit=limit)
        # enrich with conversation summary
        out = []
        for r in rows:
            conv = None
            try:
                conv = frappe.db.get_value("Heshly Network Conversation", {"network_conversation_id": r.get("network_conversation_id")}, ["network_conversation_id", "customer_name", "customer_phone", "requested_service", "location", "urgency", "preferred_time", "network_status", "qualification_state"], as_dict=True)
            except Exception:
                pass
            r["_conversation"] = conv
            out.append(r)
        return {"success": True, "dispatches": out}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_dispatch(payload=None, dispatch_id=None, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    data = _unwrap(payload, kwargs)
    dispatch_id = dispatch_id or data.get("dispatch_id") or data.get("dispatchId") or data.get("id")
    if not dispatch_id:
        return {"success": False, "message": "dispatch_id is required"}
    try:
        doc = frappe.db.get_value("Heshly Network Dispatch", {"dispatch_id": str(dispatch_id).strip()}, ["*"], as_dict=True)
        if not doc:
            return {"success": False, "message": "Dispatch not found"}
        if str(doc.get("tenant_id") or "") != tenant_id:
            # allow System Manager
            try:
                if "System Manager" not in (frappe.get_roles() or []):
                    return {"success": False, "message": "Not authorized"}
            except Exception:
                return {"success": False, "message": "Not authorized"}
        conv = None
        try:
            conv = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": doc.get("network_conversation_id")})
            # serialize turns for assigned view
            conv_dict = conv.as_dict() if hasattr(conv, "as_dict") else {}
        except Exception:
            conv_dict = frappe.db.get_value("Heshly Network Conversation", {"network_conversation_id": doc.get("network_conversation_id")}, ["*"], as_dict=True) or {}
        return {"success": True, "dispatch": doc, "conversation": conv_dict}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def accept_dispatch(payload=None, dispatch_id=None, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    data = _unwrap(payload, kwargs)
    dispatch_id = dispatch_id or data.get("dispatch_id") or data.get("dispatchId") or data.get("id")
    if not dispatch_id:
        return {"success": False, "message": "dispatch_id is required"}
    try:
        from heshly_core.services.network.dispatch_service import accept_dispatch as _accept
        res = _accept(str(dispatch_id).strip(), tenant_id)
        return res
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def decline_dispatch(payload=None, dispatch_id=None, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    data = _unwrap(payload, kwargs)
    dispatch_id = dispatch_id or data.get("dispatch_id") or data.get("dispatchId") or data.get("id")
    if not dispatch_id:
        return {"success": False, "message": "dispatch_id is required"}
    try:
        from heshly_core.services.network.dispatch_service import decline_dispatch as _decline
        res = _decline(str(dispatch_id).strip(), tenant_id)
        return res
    except Exception as e:
        return {"success": False, "message": str(e)}
