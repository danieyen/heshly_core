from __future__ import annotations

import frappe

from typing import Any

from heshly_core.services.tenant.tenant_context import TenantContext


def _tenant_has_permission(doc: Any) -> bool:
    tenant_id = TenantContext().get()
    document_tenant_id = getattr(doc, "tenant_id", None)

    frappe.logger().debug(
        f"TENANT CHECK: context={tenant_id}, document={document_tenant_id}"
    )

    if not tenant_id:
        return False

    if not document_tenant_id:
        return False

    return document_tenant_id == tenant_id


def business_account_has_permission(
    doc: Any,
    ptype: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> bool:
    if ptype == "create":
        return True

    current_user = user or frappe.session.user

    if not current_user or current_user == "Guest":
        return False

    tenant_id = TenantContext().get()

    if not tenant_id:
        return False

    document_tenant_id = getattr(doc, "tenant_id", None)

    frappe.logger().debug(
        f"BUSINESS ACCOUNT CHECK: "
        f"user={current_user}, "
        f"context_tenant={tenant_id}, "
        f"document_tenant={document_tenant_id}, "
        f"ptype={ptype}"
    )

    return document_tenant_id == tenant_id


def custom_domain_has_permission(
    doc: Any,
    ptype: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> bool:
    current_user = user or frappe.session.user

    if not current_user or current_user == "Guest":
        return False

    tenant_id = TenantContext().get()

    if not tenant_id:
        return False

    # Allow creation only when the document is being
    # created inside an active tenant context.
    #
    # The CustomDomain.validate() method will additionally
    # verify that the submitted tenant/business belong
    # to this active tenant.
    if ptype == "create":
        return True

    document_tenant_id = getattr(doc, "tenant_id", None)

    frappe.logger().debug(
        f"CUSTOM DOMAIN CHECK: "
        f"user={current_user}, "
        f"context_tenant={tenant_id}, "
        f"document_tenant={document_tenant_id}, "
        f"ptype={ptype}"
    )

    if not document_tenant_id:
        return False

    return document_tenant_id == tenant_id

def heshly_whatsapp_number_has_permission(
    doc: Any,
    ptype: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> bool:
    return _tenant_has_permission(doc)


def heshly_whatsapp_configuration_has_permission(
    doc: Any,
    ptype: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> bool:
    return _tenant_has_permission(doc)


def heshly_workflow_version_has_permission(
    doc: Any,
    ptype: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> bool:
    return _tenant_has_permission(doc)


def heshly_workflow_assignment_has_permission(
    doc: Any,
    ptype: str | None = None,
    user: str | None = None,
    debug: bool = False,
) -> bool:
    return _tenant_has_permission(doc)


def _custom_tenant_has_permission(doc: Any, field: str = "custom_heshly_tenant_id") -> bool:
    tenant_id = TenantContext().get()
    document_tenant_id = getattr(doc, field, None)
    if not tenant_id or not document_tenant_id:
        return False
    return str(document_tenant_id) == str(tenant_id)


def ai_conversation_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    return _tenant_has_permission(doc)


def ai_session_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    return _tenant_has_permission(doc)


def heshly_whatsapp_activity_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    return _tenant_has_permission(doc)


def heshly_subscription_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    return _tenant_has_permission(doc)


def business_knowledge_profile_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    return _tenant_has_permission(doc)


def ai_configuration_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    return _tenant_has_permission(doc)


def appointment_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    return _custom_tenant_has_permission(doc, "custom_heshly_tenant_id")


def event_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    return _custom_tenant_has_permission(doc, "custom_heshly_tenant_id")


def lead_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    # Administrator / System Manager bypass
    _u = user or getattr(frappe.session, "user", None) if hasattr(frappe, "session") else None  # type: ignore
    try:
        if _u == "Administrator":
            return True
        roles = frappe.get_roles(_u) if _u else frappe.get_roles()  # type: ignore
        if "System Manager" in (roles or []):
            return True
    except Exception:
        pass
    return _custom_tenant_has_permission(doc, "custom_heshly_tenant_id")


def heshly_calendar_connection_has_permission(doc: Any, ptype=None, user=None, debug=False) -> bool:
    if ptype == "create":
        return True
    return _tenant_has_permission(doc)
