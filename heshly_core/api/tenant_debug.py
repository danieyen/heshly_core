from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext

@frappe.whitelist(allow_guest=True)
def current_tenant():
    value = TenantContext().get()

    return {
        "ok": True,
        "tenant_repr": repr(value),
        "tenant_type": type(value).__name__,
        "is_string": isinstance(value, str),
    }
