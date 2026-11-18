from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


def _is_platform_admin() -> bool:
    # Require Administrator or session on HESHLY tenant app.heshly.com with_business HESHLY
    user = frappe.session.user
    if user == "Administrator":
        return True
    tenant = None
    try:
        tenant = TenantContext().get()
    except Exception:
        pass
    if tenant == "heshly":
        # Also require business HESHLY membership
        biz = frappe.session.data.get("heshly_business_id")
        if biz == "HESHLY":
            # Check membership is Owner/Administrator
            role = frappe.db.get_value("User Business Membership", {"user": user, "business_id": "HESHLY", "tenant_id": "heshly", "active": 1}, "role")
            if role in ("Owner", "Administrator"):
                return True
    # Also allow System Manager via has_permission fallback
    try:
        if "System Manager" in frappe.get_roles(user):
            return True
    except Exception:
        pass
    return False


@frappe.whitelist(allow_guest=False)
def list_whatsapp_connections():
    if not _is_platform_admin():
        frappe.throw("Not permitted.", frappe.PermissionError)
    rows = frappe.get_all("Heshly WhatsApp Number", fields=["tenant_id","business_id","phone_number","phone_number_id","waba_id","connection_status","active","configuration_id"], order_by="tenant_id asc")
    # Attach domain from Business Account
    for r in rows:
        try:
            dom = frappe.db.get_value("Business Account", {"business_id": r["business_id"]}, "domain")
            r["domain"] = dom
        except Exception:
            r["domain"] = None
    return rows
