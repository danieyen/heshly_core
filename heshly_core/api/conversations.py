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
            if any(k in body for k in ("conversation_id", "conversationId", "customer_id", "message", "tenant_id", "Business", "Conversation")):
                return body
            if "data" in body and isinstance(body["data"], dict):
                return body["data"]
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("conversation_id", "conversationId", "customer_id", "Conversation")):
                return inner
        if "data" in payload and isinstance(payload["data"], dict):
            inner = payload["data"]
            if any(k in inner for k in ("conversation_id", "Conversation", "conversation", "customer_id", "tenant_id")):
                return inner
            return inner
        if any(k in payload for k in ("Conversation", "Business")):
            return payload
    if isinstance(payload, dict):
        return payload
    return {}


def _resolve_tenant_id(data: dict) -> str | None:
    for k in ("tenant_id", "tenantId"):
        if k in data and isinstance(data[k], str) and data[k].strip():
            return data[k].strip()
    for bkey in ("business", "Business"):
        if bkey in data and isinstance(data[bkey], dict):
            b = data[bkey]
            for tk in ("tenant_id", "tenantId", "id"):
                if tk in b and isinstance(b[tk], str) and b[tk].strip():
                    return b[tk].strip()
    return None


class ConversationAPI:
    """
    Conversation API Layer for n8n.

    Provides conversation operations with tolerant input handling.
    Handles JSON strings, $json.body/data nesting, capitalized keys, and string status.
    Always returns boolean success where applicable.
    """

    def __init__(self, tenant_context: TenantContext | None = None, manager: ConversationManager | None = None):
        self.tenant_context = tenant_context or TenantContext()
        self.manager = manager or ConversationManager()

    def get(self, payload: Any) -> dict | None:
        data = _extract_payload(payload)
        conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id") or data.get("conversation_id")
        # also check Conversation object
        if not conversation_id:
            for ckey in ("conversation", "Conversation"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    conversation_id = c.get("id") or c.get("conversation_id") or c.get("conversationId")
                    if conversation_id:
                        break
        if not conversation_id:
            if isinstance(payload, str) and payload.strip():
                # handle JSON string payload that is just id
                parsed = _parse_json_if_string(payload)
                if isinstance(parsed, str) and parsed.strip():
                    conversation_id = parsed.strip()
                elif isinstance(payload, str) and payload.strip():
                    conversation_id = payload.strip()
        if not conversation_id:
            return None

        tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
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
        tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id")
        customer_id = data.get("customer_id") or data.get("customerId") or data.get("customer_id")

        # also check nested Conversation/Customer
        if not conversation_id:
            for ckey in ("conversation", "Conversation"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    conversation_id = c.get("id") or c.get("conversation_id") or c.get("conversationId")
                    if conversation_id:
                        break
        if not customer_id:
            for ckey in ("customer", "Customer"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    customer_id = c.get("id") or c.get("customer_id") or c.get("customerId")
                    if customer_id:
                        break
        # also check lead
        if not customer_id:
            for lkey in ("lead", "Lead"):
                if lkey in data and isinstance(data[lkey], dict):
                    l = data[lkey]
                    customer_id = l.get("id") or l.get("lead_id")
                    if customer_id:
                        break

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
        tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        conversation_id = data.get("conversation_id") or data.get("conversationId")
        if not conversation_id:
            for ckey in ("conversation", "Conversation"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    conversation_id = c.get("id") or c.get("conversation_id")
                    if conversation_id:
                        break
        message = data.get("message") or data.get("text") or data.get("body")
        # handle message object
        if isinstance(message, dict):
            message = message.get("text") or message.get("body") or str(message)
        role = data.get("role") or "user"
        if isinstance(role, dict):
            role = "user"

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
        tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
        if tenant_id:
            try:
                self.tenant_context.set(tenant_id)
            except Exception:
                pass

        conversation_id = data.get("conversation_id") or data.get("conversationId")
        if not conversation_id:
            for ckey in ("conversation", "Conversation"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    conversation_id = c.get("id") or c.get("conversation_id")
                    if conversation_id:
                        break
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
