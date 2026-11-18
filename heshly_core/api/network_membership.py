"""Network membership APIs — tenant-scoped."""

from __future__ import annotations

import json
from datetime import datetime, UTC
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


def _now():
    return datetime.now(UTC)


@frappe.whitelist()
def get_my_membership():
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    try:
        row = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["*"], as_dict=True)
        if not row:
            return {"success": True, "membership": None}
        return {"success": True, "membership": row}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def join_network(service_area=None, accepts_network_leads=1, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    try:
        biz = frappe.db.get_value("Business Account", {"tenant_id": tenant_id}, ["business_id", "business_name"], as_dict=True)
        business_id = (biz.get("business_id") if biz else None) or tenant_id
        existing = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["name"], as_dict=False)
        if existing:
            doc = frappe.get_doc("Heshly Network Membership", existing)
            doc.status = "Active"
            if service_area is not None:
                doc.service_area = str(service_area)[:200]
            doc.accepts_network_leads = 1 if accepts_network_leads else 0
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": "Membership updated", "membership_id": doc.membership_id}
        import uuid
        mid = f"hmem_{uuid.uuid4().hex[:10]}"
        doc = frappe.get_doc({
            "doctype": "Heshly Network Membership",
            "membership_id": mid,
            "tenant_id": tenant_id,
            "business_id": business_id,
            "status": "Active",
            "service_area": str(service_area)[:200] if service_area else "",
            "accepts_network_leads": 1 if accepts_network_leads else 1,
            "joined_at": _now(),
            "updated_at": _now(),
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Joined network", "membership_id": mid}
    except Exception as e:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def pause_network(**kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    try:
        name = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["name"], as_dict=False)
        if not name:
            return {"success": False, "message": "No membership found"}
        doc = frappe.get_doc("Heshly Network Membership", name)
        doc.status = "Paused"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Network paused"}
    except Exception as e:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def update_network_preferences(service_area=None, accepts_network_leads=None, **kwargs):
    try:
        tenant_id = _get_tenant()
    except Exception as e:
        return {"success": False, "message": str(e)}
    try:
        name = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["name"], as_dict=False)
        if not name:
            return {"success": False, "message": "No membership found"}
        doc = frappe.get_doc("Heshly Network Membership", name)
        if service_area is not None:
            doc.service_area = str(service_area)[:200]
        if accepts_network_leads is not None:
            doc.accepts_network_leads = 1 if accepts_network_leads else 0
        doc.updated_at = _now()
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "message": "Preferences updated"}
    except Exception as e:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return {"success": False, "message": str(e)}
