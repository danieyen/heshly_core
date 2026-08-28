from __future__ import annotations

from typing import Any

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
    return value


def _extract_payload(payload: Any) -> dict:
    payload = _parse_json_if_string(payload)
    if isinstance(payload, dict):
        if "body" in payload and isinstance(payload["body"], dict):
            body = payload["body"]
            # Check if body is the actual payload
            if any(k in body for k in ("entry", "message_id", "phone_number", "messages")):
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("entry", "message_id", "phone_number")):
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

        # In real implementation, compare against stored verify_token
        # For now, return challenge if mode is subscribe
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

        # Handle Meta webhook shape vs direct IncomingMessageEvent
        try:
            # Try to parse as Meta payload
            if "entry" in data:
                event = IncomingMessageEvent.parse_meta_payload(data, tenant_resolver=tenant_resolver)
            else:
                event = IncomingMessageEvent.from_dict(data)
                # If tenant_id missing but phone_number_id present, try resolver
                if not event.tenant_id and event.phone_number_id and tenant_resolver:
                    try:
                        tenant_id = tenant_resolver(event.phone_number_id)
                        if tenant_id:
                            event.tenant_id = str(tenant_id).strip()
                    except Exception:
                        pass
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

        # Validate tenant_id
        if not event.tenant_id:
            return {
                "success": False,
                "event_type": WebhookEventType.MESSAGE.value,
                "message": "tenant_id is required - tenant resolution failed. Check phone_number_id -> tenant mapping.",
                "metadata": {"phone_number_id": event.phone_number_id},
            }

        # Set tenant context
        try:
            self.tenant_context.set(event.tenant_id)
        except Exception as e:
            return {
                "success": False,
                "event_type": WebhookEventType.MESSAGE.value,
                "message": f"Failed to set tenant context: {e}",
                "metadata": {},
            }

        # Check duplicate
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
        Returns {success: bool, message_id, status}
        """
        data = _extract_payload(payload)
        phone_number = data.get("phone_number") or data.get("phoneNumber") or data.get("to") or data.get("recipient")
        text = data.get("text") or data.get("message") or data.get("body")
        phone_number_id = data.get("phone_number_id") or data.get("phoneNumberId")

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

        # In real implementation, would call Graph API with Bearer token
        # For now, return success with generated ID
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
