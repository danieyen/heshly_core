from __future__ import annotations

from typing import Any

import frappe

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


def _collect_params(explicit: dict, kwargs: dict) -> dict:
    """Merge explicit args + kwargs + n8n wrapping into single dict."""
    data: dict = {}
    # kwargs may contain body/json/data wrapping
    if kwargs:
        # if kwargs is already the payload (frappe passes query params as kwargs)
        data.update(kwargs)
        # also handle nested wrapping inside kwargs
        wrapped = _extract_payload(kwargs)
        # _extract_payload returns same dict if no wrapping, so merge wrapped keys
        for k, v in wrapped.items():
            if k not in data or not data[k]:
                data[k] = v
    for k, v in explicit.items():
        if v is not None and v != "":
            data[k] = v
    # also handle case where one of the values is a JSON string
    for k, v in list(data.items()):
        parsed = _parse_json_if_string(v)
        if isinstance(parsed, dict):
            # merge parsed dict
            for pk, pv in parsed.items():
                if pk not in data or not data[pk]:
                    data[pk] = pv
    return _extract_payload(data)


def _try_get_conversation_by_phone(manager: ConversationManager, tenant_id: str | None, phone_number: str | None, customer_id: str | None, phone_number_id: str | None) -> Any | None:
    """Try multiple manager/repository strategies to find conversation by phone/customer."""
    if not phone_number and not customer_id and not phone_number_id:
        return None
    # Try manager specific methods if they exist
    for attr in ("get_by_phone_number", "get_by_phone", "get_by_customer", "get_by_customer_id", "find_by_phone", "find_by_customer"):
        if hasattr(manager, attr):
            try:
                fn = getattr(manager, attr)
                # try with phone_number first
                for val in (phone_number, customer_id, phone_number_id):
                    if val:
                        try:
                            res = fn(str(val).strip())
                            if res:
                                return res
                        except TypeError:
                            try:
                                res = fn(str(val).strip(), tenant_id)
                                if res:
                                    return res
                            except Exception:
                                continue
                        except Exception:
                            continue
            except Exception:
                continue
    # Try list/search methods
    for attr in ("list", "search", "get_all", "find_all"):
        if hasattr(manager, attr):
            try:
                fn = getattr(manager, attr)
                for filters in (
                    {"phone_number": phone_number},
                    {"phone": phone_number},
                    {"customer_id": customer_id or phone_number},
                    {"phone_number_id": phone_number_id},
                ):
                    if not any(filters.values()):
                        continue
                    try:
                        res = fn(filters=filters)  # type: ignore
                    except TypeError:
                        try:
                            res = fn(filters)  # type: ignore
                        except Exception:
                            continue
                    except Exception:
                        continue
                    if res:
                        if isinstance(res, list) and len(res) > 0:
                            return res[0]
                        if isinstance(res, dict) and res:
                            return res
            except Exception:
                continue
    # Try frappe ORM as last resort - try common DocTypes
    try:
        for doctype in ("Heshly Conversation", "Conversation", "HeshlyConversation"):
            try:
                filters: dict = {}
                if tenant_id:
                    filters["tenant_id"] = tenant_id
                    # also try custom field
                    # we will try both
                if phone_number:
                    # try multiple field names
                    for field in ("phone_number", "phone", "customer_phone", "customer_id"):
                        try:
                            f = dict(filters)
                            f[field] = str(phone_number).strip()
                            rows = frappe.get_all(doctype, filters=f, limit=1)  # type: ignore
                            if rows:
                                doc = frappe.get_doc(doctype, rows[0].name)  # type: ignore
                                return doc
                        except Exception:
                            continue
                if customer_id:
                    for field in ("customer_id", "customer", "phone_number"):
                        try:
                            f = dict(filters)
                            f[field] = str(customer_id).strip()
                            rows = frappe.get_all(doctype, filters=f, limit=1)  # type: ignore
                            if rows:
                                doc = frappe.get_doc(doctype, rows[0].name)  # type: ignore
                                return doc
                        except Exception:
                            continue
            except Exception:
                continue
    except Exception:
        pass
    return None


def _to_dict(obj: Any) -> dict | None:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()  # type: ignore
        except Exception:
            pass
    if hasattr(obj, "as_dict"):
        try:
            return obj.as_dict()  # type: ignore
        except Exception:
            pass
    # frappe Document
    try:
        if hasattr(obj, "__dict__"):
            d = {}
            for k, v in obj.__dict__.items():
                if not k.startswith("_"):
                    try:
                        # ensure json serializable
                        import json
                        json.dumps(v)
                        d[k] = v
                    except Exception:
                        d[k] = str(v)
            if d:
                return d
    except Exception:
        pass
    return None


@frappe.whitelist(allow_guest=True)
def get(conversation_id=None, phone_number=None, phone_number_id=None, tenant_id=None, customer_id=None, **kwargs):
    """
    Whitelisted get for n8n Get Conversation History.
    Accepts conversation_id OR phone_number/customer_id + tenant_id.
    Tolerant to n8n wrapping, JSON strings, resolved_phone_number_id alias.
    tenant_id="heshly" is valid and not rejected.
    Always returns success=True with empty history when no conversation exists.
    """
    # Collect all params including aliases from n8n Normalize Payload
    explicit = {
        "conversation_id": conversation_id,
        "phone_number": phone_number,
        "phone_number_id": phone_number_id,
        "tenant_id": tenant_id,
        "customer_id": customer_id,
    }
    # handle aliases that n8n may send
    for alias in ("resolved_phone_number_id", "resolvedPhoneNumberId", "phoneNumberId", "phoneNumber", "customerId", "conversationId", "tenantId"):
        if alias in kwargs and kwargs[alias] is not None:
            # map to canonical
            if alias in ("resolved_phone_number_id", "resolvedPhoneNumberId", "phoneNumberId"):
                if not explicit.get("phone_number_id"):
                    explicit["phone_number_id"] = kwargs[alias]
            elif alias == "phoneNumber":
                if not explicit.get("phone_number"):
                    explicit["phone_number"] = kwargs[alias]
            elif alias == "customerId":
                if not explicit.get("customer_id"):
                    explicit["customer_id"] = kwargs[alias]
            elif alias == "conversationId":
                if not explicit.get("conversation_id"):
                    explicit["conversation_id"] = kwargs[alias]
            elif alias == "tenantId":
                if not explicit.get("tenant_id"):
                    explicit["tenant_id"] = kwargs[alias]

    data = _collect_params(explicit, kwargs)

    # Re-extract canonical values after wrapping normalization
    conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id")
    phone_number = data.get("phone_number") or data.get("phoneNumber") or data.get("phone") or data.get("customer_phone") or phone_number
    # also check top-level phone_number from Normalize Payload
    if not phone_number:
        phone_number = data.get("phone_number") or kwargs.get("phone_number")
    phone_number_id = data.get("phone_number_id") or data.get("phoneNumberId") or data.get("resolved_phone_number_id") or data.get("resolvedPhoneNumberId") or phone_number_id
    customer_id = data.get("customer_id") or data.get("customerId") or data.get("customer") or customer_id
    # customer_id may be phone_number for WhatsApp
    if not customer_id and phone_number:
        customer_id = phone_number
    tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId") or tenant_id
    # also handle case where tenant_id is passed as "heshly" - keep it
    if tenant_id is not None:
        tenant_id = str(tenant_id).strip()
        if tenant_id == "":
            tenant_id = None

    # Set tenant context if available (do not default to heshly, but accept heshly if provided)
    tenant_context = TenantContext()
    if tenant_id:
        try:
            tenant_context.set(tenant_id)
        except Exception:
            pass

    manager = ConversationManager(tenant_context=tenant_context) if tenant_id else ConversationManager()

    # 1) Try direct conversation_id lookup
    if conversation_id:
        try:
            cid = str(conversation_id).strip()
            if cid:
                conv = manager.get(cid)
                if conv:
                    d = _to_dict(conv) or {}
                    # normalize messages/history
                    messages = d.get("messages") or d.get("history") or d.get("conversation_history") or []
                    return {
                        "success": True,
                        "conversation": d,
                        "messages": messages,
                        "history": messages,
                        "conversation_id": d.get("conversation_id") or d.get("id") or cid,
                        "phone_number": d.get("phone_number") or phone_number,
                        "tenant_id": tenant_id,
                        "phone_number_id": phone_number_id,
                    }
        except Exception:
            pass
        # if conversation_id provided but not found, return empty success (not error) to allow workflow to continue
        return {
            "success": True,
            "conversation": None,
            "messages": [],
            "history": [],
            "conversation_id": str(conversation_id).strip(),
            "phone_number": phone_number,
            "tenant_id": tenant_id,
            "phone_number_id": phone_number_id,
            "message": "Conversation not found",
        }

    # 2) Try phone/customer lookup
    if phone_number or customer_id or phone_number_id:
        try:
            conv = _try_get_conversation_by_phone(manager, tenant_id, str(phone_number).strip() if phone_number else None, str(customer_id).strip() if customer_id else None, str(phone_number_id).strip() if phone_number_id else None)
            if conv:
                d = _to_dict(conv)
                if d is not None:
                    messages = d.get("messages") or d.get("history") or d.get("conversation_history") or []
                    return {
                        "success": True,
                        "conversation": d,
                        "messages": messages,
                        "history": messages,
                        "conversation_id": d.get("conversation_id") or d.get("id") or d.get("name"),
                        "phone_number": d.get("phone_number") or phone_number,
                        "tenant_id": tenant_id or d.get("tenant_id"),
                        "phone_number_id": d.get("phone_number_id") or phone_number_id,
                    }
                # if conv is frappe doc but _to_dict failed, try as_dict
                try:
                    d2 = conv.as_dict()  # type: ignore
                    messages = d2.get("messages") or []
                    return {
                        "success": True,
                        "conversation": d2,
                        "messages": messages,
                        "history": messages,
                        "conversation_id": d2.get("name") or d2.get("conversation_id"),
                        "phone_number": phone_number,
                        "tenant_id": tenant_id,
                        "phone_number_id": phone_number_id,
                    }
                except Exception:
                    pass
        except Exception:
            pass
        # No conversation found yet - this is valid for new WhatsApp contact, return empty history with success
        return {
            "success": True,
            "conversation": None,
            "messages": [],
            "history": [],
            "phone_number": str(phone_number).strip() if phone_number else None,
            "customer_id": str(customer_id).strip() if customer_id else None,
            "tenant_id": tenant_id,
            "phone_number_id": str(phone_number_id).strip() if phone_number_id else None,
            "message": "No conversation history",
        }

    # 3) No identifier provided - return invalid request with clear message (but success=False)
    return {
        "success": False,
        "message": "conversation_id or phone_number is required",
        "phone_number": phone_number,
        "tenant_id": tenant_id,
        "phone_number_id": phone_number_id,
    }


@frappe.whitelist(allow_guest=True)
def get_history(**kwargs):
    """Alias for get to support workflows calling get_history."""
    return get(**kwargs)


@frappe.whitelist(allow_guest=True)
def create(**kwargs):
    data = _collect_params({}, kwargs)
    tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
    if tenant_id:
        try:
            TenantContext().set(str(tenant_id).strip())
        except Exception:
            pass
    api = ConversationAPI()
    return api.create(data)


@frappe.whitelist(allow_guest=True)
def add_message(**kwargs):
    data = _collect_params({}, kwargs)
    tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
    if tenant_id:
        try:
            TenantContext().set(str(tenant_id).strip())
        except Exception:
            pass
    api = ConversationAPI()
    return api.add_message(data)


@frappe.whitelist(allow_guest=True)
def set_status(**kwargs):
    data = _collect_params({}, kwargs)
    tenant_id = _resolve_tenant_id(data) or data.get("tenant_id") or data.get("tenantId")
    if tenant_id:
        try:
            TenantContext().set(str(tenant_id).strip())
        except Exception:
            pass
    api = ConversationAPI()
    return api.set_status(data)


@frappe.whitelist(allow_guest=True)
def health(**kwargs):
    return ConversationAPI().health()
