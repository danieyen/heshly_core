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
        Normalizes Meta payload, resolves tenant, validates signature, checks duplicates.
        Returns {success: bool, event_type, message, metadata} with boolean.
        """
        data = _extract_payload(payload)
        # Enforce X-Hub-Signature-256 only when present; prefer Number's secret, fallback to Configuration
        try:
            # headers may be passed explicitly or via frappe.request.headers
            _headers = headers or {}
            if not _headers and hasattr(frappe, "request") and hasattr(frappe.request, "headers"):
                _headers = dict(getattr(frappe.request, "headers", {}) or {})
                # Werkzeug headers are case-insensitive, normalize lower
                _headers = {k.lower(): v for k, v in _headers.items()}
            _sig = _headers.get("x-hub-signature-256") or _headers.get("x-hub-signature") or ""
            if not _sig and isinstance(headers, dict):
                _sig = headers.get("X-Hub-Signature-256") or headers.get("x-hub-signature-256") or ""
            if _sig:
                _pnid = None
                if "entry" in data and isinstance(data["entry"], list) and data["entry"]:
                    ch = data["entry"][0].get("changes", [{}])[0].get("value", {}) if isinstance(data["entry"][0], dict) else {}
                    _pnid = ch.get("metadata", {}).get("phone_number_id") or ch.get("phone_number_id")
                _pnid = _pnid or data.get("phone_number_id") or data.get("phoneNumberId")
                if _pnid:
                    _cfg = None
                    try:
                        # Try Number first (has waba/app_secret via linked Configuration)
                        _num = frappe.db.get_value("Heshly WhatsApp Number", {"phone_number_id": str(_pnid).strip(), "active": 1}, ["configuration_id", "phone_number_id"], as_dict=True)
                        if _num and _num.configuration_id:
                            _cfg = frappe.db.get_value("Heshly WhatsApp Configuration", {"configuration_id": _num.configuration_id}, ["app_secret"], as_dict=True)
                            if _cfg:
                                _cfg = WhatsAppConfigurationRepository().get_by_phone_number_id(str(_pnid).strip())
                    except Exception:
                        _cfg = None
                    if not _cfg:
                        try:
                            _cfg = WhatsAppConfigurationRepository().get_by_phone_number_id(str(_pnid).strip())
                        except Exception:
                            _cfg = None
                    if _cfg:
                        _app_secret = getattr(_cfg, "app_secret", None)
                        # app_secret stored as Password — get via repository may already decrypt; if empty skip verification
                        try:
                            if not _app_secret and hasattr(_cfg, "configuration_id"):
                                # try raw get_password
                                _raw = frappe.db.get_value("Heshly WhatsApp Configuration", {"configuration_id": _cfg.configuration_id}, "app_secret")
                                _app_secret = _raw
                        except Exception:
                            pass
                        if _app_secret:
                            raw_body = getattr(getattr(frappe, "request", None), "data", None)
                            if isinstance(raw_body, str):
                                raw_body = raw_body.encode("utf-8")
                            if not raw_body:
                                import json as _json
                                raw_body = _json.dumps(payload, separators=(",", ":")).encode("utf-8")
                            try:
                                ok = self.auth.verify_signature(_cfg, raw_body, _sig)
                            except ValueError:
                                ok = False
                            if not ok:
                                return {"success": False, "event_type": WebhookEventType.UNKNOWN.value, "message": "Invalid webhook signature", "metadata": {}}
        except Exception:
            pass

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
        Send a WhatsApp message through the real Meta Cloud API.

        Resolves the active WhatsApp configuration by phone_number_id
        and delegates the actual send to WhatsAppManager.
        """
        data = _extract_payload(payload)

        # Handle additional n8n wrappers.
        if not data.get("phone_number") and not data.get("phoneNumber") and not data.get("to"):
            for wrapper in ("data", "body", "json"):
                if wrapper in data and isinstance(data[wrapper], dict):
                    inner = data[wrapper]
                    if any(
                        k in inner
                        for k in (
                            "phone_number",
                            "phoneNumber",
                            "to",
                            "recipient",
                        )
                    ):
                        data = inner
                        break

        phone_number = (
            data.get("phone_number")
            or data.get("phoneNumber")
            or data.get("to")
            or data.get("recipient")
            or data.get("phone")
        )

        text = (
            data.get("text")
            or data.get("message")
            or data.get("body")
            or data.get("response")
        )

        phone_number_id = (
            data.get("phone_number_id")
            or data.get("phoneNumberId")
            or data.get("phone_numberId")
        )

        conversation_id = (
            data.get("conversation_id")
            or data.get("conversationId")
            or ""
        )

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

        if not phone_number_id:
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "message": "phone_number_id is required",
            }

        # Resolve the real tenant-specific WhatsApp configuration.
        repository = WhatsAppConfigurationRepository()

        configuration = repository.get_by_phone_number_id(
            str(phone_number_id)
        )

        if not configuration:
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "message": (
                    f"No active WhatsApp configuration found for "
                    f"phone_number_id {phone_number_id}"
                ),
            }

        # Heshly conversation IDs are application-level identifiers,
        # not Frappe DocType names. Use the canonical tenant:phone
        # format when n8n does not provide an explicit conversation ID.
        if not conversation_id:
            conversation_id = (
                f"{configuration.tenant_id}:{str(phone_number).strip()}"
            )

        # Build the domain WhatsApp message.
        from heshly_core.models.whatsapp import (
            WhatsAppContact,
            WhatsAppDirection,
            WhatsAppMessage,
            WhatsAppMessageType,
        )

        message = WhatsAppMessage(
            message_id="",
            conversation_id=str(conversation_id),
            contact=WhatsAppContact(
                phone_number=str(phone_number),
            ),
            direction=WhatsAppDirection.OUTBOUND,
            message_type=WhatsAppMessageType.TEXT,
            text=str(text),
        )

        # Import here to avoid unnecessary module initialization during
        # webhook/API imports.
        from heshly_core.services.whatsapp.whatsapp_manager import (
            WhatsAppManager,
        )

        manager = WhatsAppManager()

        result = manager.send_message(
            configuration,
            message,
        )

        # Convert CloudAPISuccess / CloudAPIError into the simple
        # boolean response contract expected by n8n.
        from heshly_core.services.whatsapp.api.api_models import (
            CloudAPISuccess,
        )

        if isinstance(result, CloudAPISuccess):
            return {
                "success": True,
                "message_id": result.message_id,
                "status": "sent",
                "message": "WhatsApp message sent successfully",
                "tenant_id": configuration.tenant_id,
                "phone_number_id": configuration.phone_number_id,
            }

        return {
            "success": False,
            "message_id": None,
            "status": "failed",
            "message": getattr(
                result,
                "message",
                "WhatsApp Cloud API request failed",
            ),
            "error": getattr(
                result,
                "message",
                "WhatsApp Cloud API request failed",
            ),
            "tenant_id": configuration.tenant_id,
            "phone_number_id": configuration.phone_number_id,
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
def webhook(**kwargs):
    api = WhatsAppAPI()
    
    if frappe.request and frappe.request.method == "GET":
        result = api.verify_webhook(kwargs)
        if result.get("success") and result.get("challenge") is not None:
            return result["challenge"]
        frappe.throw(result.get("message", "Wehook verification failed"), frappe.ValidationError)
    return api.webhook(kwargs, tenant_resolver=resolve_tenant)


@frappe.whitelist(allow_guest=True)
def resolve_tenant(phone_number_id=None):
    # Canonical chain: phone_number_id → Heshly WhatsApp Number → Business Account → tenant_id
    # Falls back to Heshly WhatsApp Configuration for back-compat. Tolerant to n8n wrapping.
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
    # 1. Try canonical Number persistent table (phone_number_id unique) → Business Account → tenant_id
    try:
        num = frappe.db.get_value(
            "Heshly WhatsApp Number",
            {"phone_number_id": phone_number_id, "active": 1},
            ["tenant_id", "business_id", "phone_number_id"],
            as_dict=True,
        )
        if num and num.tenant_id and str(num.tenant_id).strip():
            # Validate Business Account still Active and matches
            biz = frappe.db.get_value(
                "Business Account",
                {"business_id": num.business_id, "status": "Active"},
                ["tenant_id"],
                as_dict=True,
            )
            if biz and str(biz.tenant_id).strip() == str(num.tenant_id).strip():
                return {"success": True, "tenant_id": str(num.tenant_id).strip(), "phone_number_id": str(num.phone_number_id).strip() or phone_number_id, "business_id": num.business_id}
    except Exception:
        pass
    # 2. Fallback to Configuration (back-compat, transient during migration)
    try:
        config = WhatsAppConfigurationRepository().get_by_phone_number_id(phone_number_id)
    except Exception:
        return {"success": False, "message": f"No active WhatsApp configuration found for phone_number_id: {phone_number_id}", "phone_number_id": phone_number_id}
    if not config:
        return {"success": False, "message": f"No active WhatsApp configuration found for phone_number_id: {phone_number_id}", "phone_number_id": phone_number_id}
    tenant_id = getattr(config, "tenant_id", None)
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

@frappe.whitelist(allow_guest=True)
def send_message(**kwargs):
    """
    Frappe API wrapper for sending a real WhatsApp message.
    """
    api = WhatsAppAPI()
    return api.send_message(kwargs)
