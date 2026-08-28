from __future__ import annotations

from typing import Any

from heshly_core.models.conversation import Conversation, ConversationStatus
from heshly_core.services.conversation.conversation_manager import ConversationManager
from heshly_core.services.tenant.tenant_context import TenantContext


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
            if any(k in body for k in ("conversation_id", "conversationId", "customer_id", "message")):
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("conversation_id", "conversationId", "customer_id")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]
    if isinstance(payload, dict):
        return payload
    return {}


class ConversationAPI:
    """
    Conversation API Layer for n8n.

    Provides conversation operations with tolerant input handling.
    Handles JSON strings, $json.body nesting, and string status.
    """

    def __init__(self, tenant_context: TenantContext | None = None, manager: ConversationManager | None = None):
        self.tenant_context = tenant_context or TenantContext()
        self.manager = manager or ConversationManager()

    def get(self, payload: Any) -> dict | None:
        data = _extract_payload(payload)
        conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id") or data.get("conversation_id")
        if not conversation_id:
            # Try payload itself as string
            if isinstance(payload, str) and payload.strip():
                conversation_id = payload.strip()
        if not conversation_id:
            return None

        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        try:
            conversation = self.manager.get(str(conversation_id))
            if conversation:
                return conversation.to_dict()
            return None
        except Exception:
            return None

    def create(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id")
        customer_id = data.get("customer_id") or data.get("customerId") or data.get("customerId")

        if not conversation_id or not customer_id:
            return {
                "success": False,
                "message": "conversation_id and customer_id are required",
            }

        try:
            conversation = self.manager.create(str(conversation_id), str(customer_id))
            return {
                "success": True,
                "conversation": conversation.to_dict(),
                "message": "Conversation created",
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
            }

    def add_message(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        conversation_id = data.get("conversation_id") or data.get("conversationId")
        message = data.get("message") or data.get("text") or data.get("body")
        role = data.get("role") or "user"

        if not conversation_id or not message:
            return {
                "success": False,
                "message": "conversation_id and message are required",
            }

        try:
            conversation = self.manager.get(str(conversation_id))
            if not conversation:
                return {
                    "success": False,
                    "message": "Conversation not found",
                }
            if role == "assistant":
                self.manager.add_assistant_message(conversation, str(message))
            elif role == "system":
                self.manager.add_system_message(conversation, str(message))
            else:
                self.manager.add_user_message(conversation, str(message))
            self.manager.save(conversation)
            return {
                "success": True,
                "conversation": conversation.to_dict(),
                "message": "Message added",
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
            }

    def set_status(self, payload: Any) -> dict:
        data = _extract_payload(payload)
        tenant_id = data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        conversation_id = data.get("conversation_id") or data.get("conversationId")
        status = data.get("status")

        if not conversation_id or not status:
            return {
                "success": False,
                "message": "conversation_id and status are required",
            }

        try:
            conversation = self.manager.get(str(conversation_id))
            if not conversation:
                return {
                    "success": False,
                    "message": "Conversation not found",
                }
            self.manager.set_status(conversation, status)
            self.manager.save(conversation)
            return {
                "success": True,
                "conversation": conversation.to_dict(),
                "message": f"Status set to {status}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
            }

    def health(self) -> dict:
        return {
            "api": "conversation_api",
            "status": "healthy",
        }
