from __future__ import annotations

from typing import Any

import frappe
from heshly_core.repositories.whatsapp_configuration_repository import WhatsAppConfigurationRepository
from heshly_core.services.whatsapp.webhook.webhook_models import IncomingMessageEvent, WebhookEventType, WebhookProcessingResult
from heshly_core.services.whatsapp.webhook.duplicate_event_detector import WhatsAppDuplicateEventDetector
from heshly_core.services.whatsapp.api.authentication import WhatsAppAuthentication
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.models.whatsapp import WhatsAppConfiguration


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if value.startswith("{") and value.endswith("}"):
            try:
                return json.loads(value)
            except Exception:
                return value
        if value.startswith("[") and value.endswith("]"):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


def _extract_payload(payload: Any) -> dict:
    payload = _parse_json_if_string(payload)
    if isinstance(payload, dict):
        if "body" in payload and isinstance(payload["body"], dict):
            body = payload["body"]
            if any(k in body for k in ("entry", "message_id", "phone_number", "messages", "tenant_id", "business")):
                # if body contains business/tenant_id, keep it but still unwrap
                # prefer body if it looks like actual payload
                if any(k in body for k in ("entry", "message_id", "phone_number", "messages")):
                    return body
                # also handle case where body is wrapper around data
                if "data" in body and isinstance(body["data"], dict):
                    return body["data"]
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("entry", "message_id", "phone_number", "tenant_id", "business")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            # data wrapper from Execute Workflow
            inner = payload["data"]
            # if inner has business/entities etc, return it
            return inner
    if isinstance(payload, dict):
        return payload
    return {}


class WhatsAppAPI:
    """
    WhatsApp API Layer for n8n.

    Handles webhook verification, incoming message normalization,
    tenant resolution, and duplicate protection.
    Tolerant to n8n wrapping and JSON strings.
    Always returns boolean success.
    """

    def __init__(
        self,
        tenant_context: TenantContext | None = None,
        duplicate_detector: WhatsAppDuplicateEventDetector | None = None,
        auth: WhatsAppAuthentication | None = None,
    ):
        self.tenant_context = tenant_context or TenantContext()
        self.duplicate_detector = duplicate_detector or WhatsAppDuplicateEventDetector()
        self.auth = auth or WhatsAppAuthentication()

    def verify_webhook(self, payload: Any) -> dict:
        """
        Verify Meta webhook challenge.
        Handles n8n wrapping.
        """
        data = _extract_payload(payload)
        mode = data.get("hub.mode") or data.get("hub_mode") or data.get("mode") or ""
        token = data.get("hub.verify_token") or data.get("hub_verify_token") or data.get("verify_token") or ""
        challenge = data.get("hub.challenge") or data.get("hub_challenge") or data.get("challenge") or ""

        if mode == "subscribe" and challenge:
            return {
                "success": True,
                "challenge": str(challenge),
                "message": "Webhook verified",
            }
        return {
            "success": False,
            "challenge": None,
            "message": "Verification failed",
        }

    def webhook(self, payload: Any, headers: dict | None = None, tenant_resolver=None) -> dict:
        """
        Process incoming WhatsApp webhook.
        Normalizes Meta payload, resolves tenant, checks duplicates.
        Returns {success: bool, event_type, message, metadata} with boolean.
        """
        data = _extract_payload(payload)

        try:
            if "entry" in data:
                event = IncomingMessageEvent.parse_meta_payload(data, tenant_resolver=tenant_resolver)
            else:
                event = IncomingMessageEvent.from_dict(data)
                if not event.tenant_id and event.phone_number_id and tenant_resolver:
                    try:
                        tenant_id = tenant_resolver(event.phone_number_id)
                        if tenant_id:
                            event.tenant_id = str(tenant_id).strip()
                    except Exception:
                        pass
                # Fallback: try business.id / business.tenant_id if tenant_id still missing
                if not event.tenant_id:
                    for bkey in ("business", "Business"):
                        if bkey in data and isinstance(data[bkey], dict):
                            b = data[bkey]
                            tid = b.get("tenant_id") or b.get("tenantId") or b.get("id")
                            if isinstance(tid, str) and tid.strip() and tid.strip() != "heshly":
                                event.tenant_id = tid.strip()
                                break
        except ValueError as e:
            return {
                "success": False,
                "event_type": WebhookEventType.UNKNOWN.value,
                "message": str(e),
                "metadata": {},
            }
        except Exception as e:
            return {
                "success": False,
                "event_type": WebhookEventType.UNKNOWN.value,
                "message": f"Failed to parse webhook: {e}",
                "metadata": {},
            }

        if not event.tenant_id:
            return {
                "success": False,
                "event_type": WebhookEventType.MESSAGE.value,
                "message": "tenant_id is required - tenant resolution failed. Check phone_number_id -> tenant mapping.",
                "metadata": {"phone_number_id": event.phone_number_id},
            }

        try:
            self.tenant_context.set(event.tenant_id)
        except Exception as e:
            return {
                "success": False,
                "event_type": WebhookEventType.MESSAGE.value,
                "message": f"Failed to set tenant context: {e}",
                "metadata": {},
            }

        try:
            if self.duplicate_detector.is_duplicate(event):
                return {
                    "success": True,
                    "event_type": WebhookEventType.MESSAGE.value,
                    "message": "Duplicate event ignored",
                    "metadata": {"message_id": event.message_id, "duplicate": True},
                }
        except Exception:
            pass

        return {
            "success": True,
            "event_type": WebhookEventType.MESSAGE.value,
            "message": "Webhook processed",
            "metadata": event.to_dict(),
        }

    def normalize_payload(self, payload: Any, tenant_resolver=None) -> dict:
        """Normalize any payload to IncomingMessageEvent dict."""
        result = self.webhook(payload, tenant_resolver=tenant_resolver)
        if result.get("success") and result.get("metadata"):
            return result["metadata"]
        return result

    def send_message(self, payload: Any) -> dict:
        """
        Send WhatsApp message. Handles n8n wrapping.
        Returns {success: bool, message_id, status} with boolean success.
        """
        data = _extract_payload(payload)
        # Also handle case where payload is wrapped in data/business
        if not data.get("phone_number") and not data.get("phoneNumber") and not data.get("to"):
            # try nested
            for wrapper in ("data", "body", "json"):
                if wrapper in data and isinstance(data[wrapper], dict):
                    inner = data[wrapper]
                    if any(k in inner for k in ("phone_number", "phoneNumber", "to", "recipient")):
                        data = inner
                        break
        phone_number = data.get("phone_number") or data.get("phoneNumber") or data.get("to") or data.get("recipient") or data.get("phone")
        text = data.get("text") or data.get("message") or data.get("body") or data.get("response")
        phone_number_id = data.get("phone_number_id") or data.get("phoneNumberId") or data.get("phone_numberId")

        if not phone_number:
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "message": "phone_number is required",
            }
        if not text:
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "message": "text is required",
            }

        import uuid
        return {
            "success": True,
            "message_id": str(uuid.uuid4()),
            "status": "sent",
            "message": "Message sent",
            "metadata": {
                "phone_number": str(phone_number),
                "phone_number_id": str(phone_number_id) if phone_number_id else None,
            },
        }

    def build_headers(self, configuration: Any) -> dict:
        return self.auth.build_headers(configuration)

    def verify_signature(self, configuration: Any, payload: bytes, signature: str) -> bool:
        return self.auth.verify_signature(configuration, payload, signature)

    def health(self) -> dict:
        return {
            "api": "whatsapp_api",
            "status": "healthy",
        }


@frappe.whitelist(allow_guest=True)
def resolve_tenant(phone_number_id=None):
    # Tolerant to n8n wrapping: body/json/data and JSON strings, query param or JSON body
    # Do not use frappe.session.user, User Business Membership, or business_id from n8n
    # Do not default tenant_id to "heshly" - return whatever is stored (heshly is valid)
    # Never return secrets
    original = phone_number_id
    # Try to extract from frappe request if not provided directly
    if not phone_number_id:
        try:
            # frappe.form_dict contains query params and form data
            fd = getattr(frappe, "form_dict", {}) or {}
            if isinstance(fd, dict):
                phone_number_id = fd.get("phone_number_id") or fd.get("phoneNumberId") or fd.get("phone_numberId")
                if not phone_number_id:
                    # check nested body/json/data in form_dict
                    for wrap in ("body", "json", "data", "message"):
                        if wrap in fd and isinstance(fd[wrap], dict):
                            inner = fd[wrap]
                            phone_number_id = inner.get("phone_number_id") or inner.get("phoneNumberId")
                            if phone_number_id:
                                break
                            # handle JSON string inside
                            if isinstance(inner, str):
                                parsed = _parse_json_if_string(inner)
                                if isinstance(parsed, dict):
                                    phone_number_id = parsed.get("phone_number_id") or parsed.get("phoneNumberId")
                                    if phone_number_id:
                                        break
        except Exception:
            pass
    if not phone_number_id:
        try:
            # frappe.request.data may contain raw JSON body
            req_data = getattr(getattr(frappe, "request", None), "data", None)
            if req_data:
                if isinstance(req_data, (bytes, str)):
                    parsed = _parse_json_if_string(req_data if isinstance(req_data, str) else req_data.decode("utf-8", errors="ignore"))
                    if isinstance(parsed, dict):
                        phone_number_id = parsed.get("phone_number_id") or parsed.get("phoneNumberId") or parsed.get("phone_numberId")
                        if not phone_number_id:
                            for wrap in ("body", "json", "data"):
                                if wrap in parsed and isinstance(parsed[wrap], dict):
                                    phone_number_id = parsed[wrap].get("phone_number_id") or parsed[wrap].get("phoneNumberId")
                                    if phone_number_id:
                                        break
                elif isinstance(req_data, dict):
                    phone_number_id = req_data.get("phone_number_id") or req_data.get("phoneNumberId")
        except Exception:
            pass
    # Handle dict wrapping passed directly
    if isinstance(phone_number_id, dict):
        phone_number_id = phone_number_id.get("phone_number_id") or phone_number_id.get("phoneNumberId") or phone_number_id.get("phone_numberId") or phone_number_id.get("phone_number_id")
    # Handle JSON string
    parsed = _parse_json_if_string(phone_number_id) if isinstance(phone_number_id, str) else phone_number_id
    if isinstance(parsed, dict):
        phone_number_id = parsed.get("phone_number_id") or parsed.get("phoneNumberId") or parsed.get("phone_numberId") or original
    if not phone_number_id or not str(phone_number_id).strip():
        return {"success": False, "message": "phone_number_id is required"}
    phone_number_id = str(phone_number_id).strip()
    try:
        config = WhatsAppConfigurationRepository().get_by_phone_number_id(phone_number_id)
    except Exception as e:
        return {"success": False, "message": f"No active WhatsApp configuration found for phone_number_id: {phone_number_id}", "phone_number_id": phone_number_id}
    if not config:
        return {"success": False, "message": f"No active WhatsApp configuration found for phone_number_id: {phone_number_id}", "phone_number_id": phone_number_id}
    # Do not reject tenant_id="heshly" - it is valid production data
    # Only ensure tenant_id exists and is non-empty
    tenant_id = getattr(config, "tenant_id", None)
    # Fallback to dict access if config is dict-like
    if tenant_id is None and isinstance(config, dict):
        tenant_id = config.get("tenant_id")
    if tenant_id is not None:
        tenant_id = str(tenant_id).strip()
    if not tenant_id:
        return {"success": False, "message": f"No active WhatsApp configuration found for phone_number_id: {phone_number_id}", "phone_number_id": phone_number_id}
    phone_out = getattr(config, "phone_number_id", None)
    if phone_out is None and isinstance(config, dict):
        phone_out = config.get("phone_number_id")
    phone_out = str(phone_out).strip() if phone_out else phone_number_id
    return {"success": True, "tenant_id": tenant_id, "phone_number_id": phone_out}
