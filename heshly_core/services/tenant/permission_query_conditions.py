from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


def _tenant_condition() -> str:
    tenant_id = TenantContext().get()

    if not tenant_id:
        return "1 = 0"

    return "tenant_id = " + frappe.db.escape(tenant_id)


def _custom_tenant_condition(field: str = "custom_heshly_tenant_id") -> str:
    tenant_id = TenantContext().get()
    if not tenant_id:
        return "1 = 0"
    return f"`{field}` = " + frappe.db.escape(tenant_id)  # type: ignore


def business_account_query(user: str | None = None) -> str:
    return _tenant_condition()

def custom_domain_query(user: str | None = None) -> str:
    return _tenant_condition()

def heshly_whatsapp_number_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_whatsapp_configuration_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_workflow_version_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_workflow_assignment_query(user: str | None = None) -> str:
    return _tenant_condition()


# --- Additional tenant-scoped queries (cover gaps) ---

def ai_conversation_query(user: str | None = None) -> str:
    return _tenant_condition()


def ai_session_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_whatsapp_activity_query(user: str | None = None) -> str:
    return _tenant_condition()


def heshly_subscription_query(user: str | None = None) -> str:
    return _tenant_condition()


def business_knowledge_profile_query(user: str | None = None) -> str:
    return _tenant_condition()


def ai_configuration_query(user: str | None = None) -> str:
    return _tenant_condition()


def appointment_query(user: str | None = None) -> str:
    return _custom_tenant_condition("custom_heshly_tenant_id")


def event_query(user: str | None = None) -> str:
    return _custom_tenant_condition("custom_heshly_tenant_id")


def _is_admin_user(user: str | None) -> bool:
    try:
        import frappe as _f
        u = user or getattr(_f.session, "user", None)  # type: ignore
        if u == "Administrator":
            return True
        # get_roles(user) when user is None returns roles for current session user
        try:
            roles = _f.get_roles(user) if user else _f.get_roles()  # type: ignore
        except Exception:
            roles = _f.get_roles()  # type: ignore
        if "System Manager" in (roles or []):
            return True
    except Exception:
        pass
    return False


def lead_query(user: str | None = None) -> str:
    # Administrator/System Manager bypass is determined by the actual session, not TenantContext
    if _is_admin_user(user):
        return ""
    # For non-admin, enforce tenant isolation via TenantContext
    return _custom_tenant_condition("custom_heshly_tenant_id")


def _admin_or_tenant_condition(field: str = "custom_heshly_tenant_id") -> str:
    # helper for appointment/event if needed separately
    return lead_query(None)


def heshly_calendar_connection_query(user: str | None = None) -> str:
    return _tenant_condition()
