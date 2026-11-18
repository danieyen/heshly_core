from __future__ import annotations

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.whatsapp.conversation_flow import (
    WhatsAppConversationFlow,
)
from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


_CONTEXT = TenantContext()
_FLOW = WhatsAppConversationFlow()


@frappe.whitelist(allow_guest=True)
def whatsapp_inbound():
    """
    Internal Heshly -> n8n WhatsApp integration endpoint.

    n8n authenticates using the configured integration token.
    The endpoint then establishes tenant context and hands the
    normalized WhatsApp event to the existing conversation flow.
    """

    expected_token = frappe.conf.get(
        "heshly_n8n_integration_token"
    )

    if not expected_token:
        frappe.throw(
            "Heshly n8n integration token is not configured.",
            frappe.ValidationError,
        )

    integration_token = (
        frappe.get_request_header(
            "X-Heshly-Integration-Token"
        )
        or ""
    )

    if integration_token != expected_token:
        frappe.throw(
            "Invalid n8n integration credentials.",
            frappe.AuthenticationError,
        )

    payload = frappe.request.get_json(
        silent=True
    ) or {}

    tenant_id = (
        payload.get("tenant_id")
        or ""
    ).strip()

    if not tenant_id:
        frappe.throw(
            "tenant_id is required.",
            frappe.ValidationError,
        )

    event = IncomingMessageEvent(
        tenant_id=tenant_id,
        phone_number=(
            payload.get("phone_number")
            or ""
        ),
        customer_name=(
            payload.get("customer_name")
        ),
        message_id=(
            payload.get("message_id")
            or ""
        ),
        message_type=(
            payload.get("message_type")
            or "text"
        ),
        text=(
            payload.get("text")
            or ""
        ),
        timestamp=payload.get(
            "timestamp"
        ),
        phone_number_id=(
            payload.get("phone_number_id")
        ),
    )

    if not event.phone_number:
        frappe.throw(
            "phone_number is required.",
            frappe.ValidationError,
        )

    if not event.message_id:
        frappe.throw(
            "message_id is required.",
            frappe.ValidationError,
        )

    if not event.text:
        frappe.throw(
            "text is required.",
            frappe.ValidationError,
        )

    _CONTEXT.clear()
    _CONTEXT.set(tenant_id)

    try:
        result = _FLOW.process(
            event,
            tenant_id=tenant_id,
        )

        return {
            "success": True,
            "tenant_id": tenant_id,
            "result": result,
        }

    finally:
        _CONTEXT.clear()
