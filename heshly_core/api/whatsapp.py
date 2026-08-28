from __future__ import annotations

import uuid

import frappe

from werkzeug.wrappers import Response

from heshly_core.repositories.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepository,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.whatsapp.webhook.webhook_integration import (
    WhatsAppWebhookIntegration,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    WebhookVerificationRequest,
)

from heshly_core.models.whatsapp import (
    WhatsAppContact,
    WhatsAppDirection,
    WhatsAppMessage,
    WhatsAppMessageType,
)

from heshly_core.services.whatsapp.whatsapp_manager import (
    WhatsAppManager,
)


_CONFIGURATIONS = WhatsAppConfigurationRepository()
_CONTEXT = TenantContext()
_WEBHOOKS = WhatsAppWebhookIntegration()
_MANAGER = WhatsAppManager()


@frappe.whitelist(allow_guest=True, methods=["POST"])
def send_message(
    phone_number: str,
    message: str,
    phone_number_id: str | None = None,
):
    """
    Send an outbound WhatsApp text message for the
    currently authenticated Heshly tenant.

    Flow:

        API
          -> TenantContext
          -> WhatsAppConfiguration
          -> WhatsAppManager
          -> WhatsAppOutgoingMessageSender
          -> Meta Cloud API
          -> WhatsAppActivityLogger
          -> Heshly WhatsApp Activity
    """

    if not phone_number or not phone_number.strip():
        frappe.throw("Phone number is required.")

    if not message or not message.strip():
        frappe.throw("Message is required.")

    phone_number = phone_number.strip()
    message = message.strip()

    # Resolve tenant from the WhatsApp phone number.
    # n8n calls this endpoint without a Frappe login session.
    if phone_number_id:
        configuration = _CONFIGURATIONS.get_by_phone_number_id(
            phone_number_id.strip()
        )

        if configuration:
            tenant_id = configuration.tenant_id
    else:
        tenant_id = _CONTEXT.require()

        configuration = _CONFIGURATIONS.get(
            tenant_id
        )

    if configuration is None:
        frappe.throw(
            f"No active WhatsApp configuration found "
            f"for tenant '{tenant_id}'."
        )

    if not configuration.business_id:
        frappe.throw(
            "WhatsApp configuration has no business_id."
        )

    outgoing = WhatsAppMessage(
        message_id=str(uuid.uuid4()),
        conversation_id=f"{tenant_id}:{phone_number}",
        contact=WhatsAppContact(
            phone_number=phone_number,
        ),
        direction=WhatsAppDirection.OUTBOUND,
        message_type=WhatsAppMessageType.TEXT,
        text=message,
    )

    result = _MANAGER.send_message(
        configuration,
        outgoing,
    )

    if hasattr(result, "message_id"):
        meta_message_id = result.message_id
    else:
        meta_message_id = None

    if hasattr(result, "success") and result.success:
        return {
            "success": True,
            "message_id": meta_message_id,
            "conversation_id": outgoing.conversation_id,
        }

    category = getattr(result, "category", None)

    if category is not None and hasattr(category, "value"):
        category = category.value

    return {
        "success": False,
        "message_id": meta_message_id,
        "conversation_id": outgoing.conversation_id,
        "error": {
            "code": getattr(result, "code", None),
            "message": getattr(
                result,
                "message",
                "WhatsApp message failed.",
            ),
            "category": category,
            "retryable": getattr(
                result,
                "retryable",
                False,
            ),
        },
    }


@frappe.whitelist(allow_guest=True)
def webhook():

    print("HESHLY WEBHOOK ENTERED", frappe.request.method, flush=True)
    """
    Public Meta WhatsApp webhook endpoint.

    GET:
        Meta webhook verification.

    POST:
        Incoming WhatsApp events.
    """

    method = frappe.request.method

    # =================================================
    # META VERIFICATION
    # =================================================

    if method == "GET":

        mode = frappe.form_dict.get(
            "hub.mode"
        )

        token = frappe.form_dict.get(
            "hub.verify_token"
        )

        challenge = frappe.form_dict.get(
            "hub.challenge"
        )

        if mode != "subscribe":
            return Response(
                "Forbidden",
                status=403,
                content_type="text/plain",
            )

        configuration = _find_configuration_by_verify_token(
            token
        )

        if configuration is None:
            return Response(
                "Forbidden",
                status=403,
                content_type="text/plain",
            )

        result = _WEBHOOKS.verify(
            configuration,
            WebhookVerificationRequest(
                mode=mode,
                verify_token=token or "",
                challenge=challenge or "",
            ),
        )

        if not result.success:
            return Response(
                "Forbidden",
                status=403,
                content_type="text/plain",
            )

        return Response(
            result.challenge or "",
            status=200,
            content_type="text/plain",
        )

    # =================================================
    # INCOMING WEBHOOK
    # =================================================

    if method == "POST":

        print(
            "HESHLY POST DEBUG | request=" +
            repr(frappe.request),
            flush=True,
        )

        try:
            raw_payload = frappe.request.get_data(
                cache=True
            )
            print(
                "HESHLY POST DEBUG | raw_bytes=" +
                str(len(raw_payload)),
                flush=True,
            )
        except Exception:
            print(
                "HESHLY POST DEBUG | get_data FAILED",
                flush=True,
            )
            raise

        print(
            "HESHLY POST DEBUG | STEP=before_headers",
            flush=True,
        )

        signature = frappe.request.headers.get(
            "X-Hub-Signature-256",
            "",
        )

        print(
            "HESHLY POST DEBUG | STEP=after_headers | "
            f"signature_present={bool(signature)}",
            flush=True,
        )

        try:
            print(
                "HESHLY POST DEBUG | STEP=before_parse",
                flush=True,
            )

            import json

            payload = json.loads(
                raw_payload.decode("utf-8")
            )

            print(
                "HESHLY POST DEBUG | STEP=after_parse | "
                f"type={type(payload).__name__}",
                flush=True,
            )
        except Exception:
            return Response(
                "Invalid JSON",
                status=400,
                content_type="text/plain",
            )

        # =================================================
        # DEBUG: HTTP CONFIGURATION RESOLUTION
        # =================================================

        try:
            debug_phone_number_id = (
                payload.get("entry", [{}])[0]
                .get("changes", [{}])[0]
                .get("value", {})
                .get("metadata", {})
                .get("phone_number_id")
            )

            debug_repo_result = (
                _WEBHOOKS._configurations
                .get_by_phone_number_id(
                    debug_phone_number_id
                )
            )

            debug_direct_db = frappe.db.get_value(
                "Heshly WhatsApp Configuration",
                {
                    "phone_number_id": debug_phone_number_id,
                    "active": 1,
                },
                "name",
            )

            frappe.logger("whatsapp_webhook").error(
                "HTTP WEBHOOK DEBUG | "
                f"phone={debug_phone_number_id!r} | "
                f"repo={debug_repo_result!r} | "
                f"direct_db={debug_direct_db!r} | "
                f"user={frappe.session.user!r}"
            )

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "WhatsApp HTTP resolution DEBUG failed",
            )

        debug_phone = (
            payload.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("metadata", {})
            .get("phone_number_id")
        )

        print(
            "HESHLY WEBHOOK RESOLUTION | "
            f"phone={debug_phone!r} | "
            f"type={type(debug_phone).__name__}",
            flush=True,
        )

        debug_repo = (
            _WEBHOOKS._configurations
            .get_by_phone_number_id(
                debug_phone
            )
        )

        print(
            "HESHLY WEBHOOK REPO RESULT | "
            f"result={debug_repo!r}",
            flush=True,
        )

        configuration = (
            _WEBHOOKS.configuration_for_payload(
                payload
            )
        )

        print(
            "HESHLY WEBHOOK CONFIGURATION | "
            f"configuration={configuration!r}",
            flush=True,
        )

        if configuration is None:
            frappe.logger().error(
                "WhatsApp webhook configuration "
                "not found for phone_number_id."
            )

            return Response(
                "Unknown WhatsApp phone number",
                status=404,
                content_type="text/plain",
            )

        # -------------------------------------------------
        # Verify Meta signature
        # -------------------------------------------------

        if not _WEBHOOKS._verification.verify_signature(
            configuration,
            raw_payload,
            signature,
        ):
            frappe.logger().error(
                "Invalid WhatsApp webhook signature."
            )

            return Response(
                "Invalid signature",
                status=403,
                content_type="text/plain",
            )

        # -------------------------------------------------
        # Establish tenant context
        # -------------------------------------------------

        _CONTEXT.clear()
        _CONTEXT.set(
            configuration.tenant_id
        )

        try:
            result = _WEBHOOKS.process(
                payload
            )

            return {
                "success": result.success,
                "event_type": result.event_type.value,
                "message": result.message,
                "metadata": result.metadata,
            }

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "WhatsApp webhook processing failed",
            )

            return Response(
                "Webhook processing failed",
                status=500,
                content_type="text/plain",
            )

        finally:
            _CONTEXT.clear()

    return Response(
        "Method Not Allowed",
        status=405,
        content_type="text/plain",
    )


def _find_configuration_by_verify_token(
    verify_token: str | None,
):
    """
    Resolve Meta GET verification to an active
    WhatsApp configuration.

    Verify tokens are stored encrypted in Frappe,
    therefore this performs the comparison after
    loading candidate active configurations.
    """

    if not verify_token:
        return None

    names = frappe.get_all(
        "Heshly WhatsApp Configuration",
        filters={
            "active": 1,
        },
        pluck="name",
    )

    for name in names:
        doc = frappe.get_doc(
            "Heshly WhatsApp Configuration",
            name,
        )

        stored_token = (
            doc.get_password("verify_token")
            if doc.verify_token
            else ""
        )

        if stored_token == verify_token:
            return _CONFIGURATIONS._to_model(
                doc
            )

    return None

@frappe.whitelist(allow_guest=True)
def resolve_tenant(phone_number_id):
    """
    Resolve Heshly tenant/business from a WhatsApp phone_number_id.
    """

    if not phone_number_id:
        frappe.throw("phone_number_id is required")

    configuration = _CONFIGURATIONS.get_by_phone_number_id(
        phone_number_id
    )

    if configuration is None:
        frappe.throw(
            f"No active WhatsApp configuration found for "
            f"phone_number_id '{phone_number_id}'."
        )

    if not configuration.tenant_id:
        frappe.throw("WhatsApp configuration has no tenant_id.")

    if not configuration.business_id:
        frappe.throw("WhatsApp configuration has no business_id.")

    return {
        "success": True,
        "tenant_id": configuration.tenant_id,
        "business_id": configuration.business_id,
        "phone_number_id": configuration.phone_number_id,
    }
