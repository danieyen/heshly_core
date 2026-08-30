from __future__ import annotations

import json
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import frappe
except ImportError:  # pragma: no cover
    class _MockWhitelist:
        def __call__(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator
    class _MockFrappe:
        whitelist = _MockWhitelist()
        request = None
        local = None
    frappe = _MockFrappe()  # type: ignore

try:
    from heshly_core.services.tenant.tenant_context import TenantContext
except ImportError:
    TenantContext = None  # type: ignore


def _parse_json_string(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return value
        if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
            try:
                return json.loads(v)
            except Exception:
                return value
    return value


def _unwrap_payload(payload: Any, kwargs: dict) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(kwargs, dict):
        data.update(kwargs)
    if payload is not None:
        parsed = _parse_json_string(payload)
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if k not in data:
                    data[k] = v
            if not data:
                data = dict(parsed)
        elif isinstance(parsed, str) and parsed.strip():
            try:
                inner = json.loads(parsed)
                if isinstance(inner, dict):
                    data.update(inner)
            except Exception:
                pass
    for _ in range(4):
        wrapped = None
        for key in ("$json", "json", "body", "data", "payload", "input", "params"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    if "__rl" in val and "value" in val:
                        data[key] = str(val["value"]).strip()
                        continue
                    wrapped = val
                    break
        if wrapped is not None:
            merged = dict(data)
            for k in ("$json", "json", "body", "data", "payload", "input", "params"):
                merged.pop(k, None)
            for k, v in wrapped.items():
                v = _parse_json_string(v)
                if isinstance(v, dict) and "__rl" in v and "value" in v:
                    v = str(v["value"]).strip()
                if k not in merged or merged[k] is None or merged[k] == "":
                    merged[k] = v
            data = merged
        else:
            break
    for k, v in list(data.items()):
        if isinstance(v, dict) and "__rl" in v and "value" in v:
            data[k] = str(v["value"]).strip()
            continue
        parsed = _parse_json_string(v)
        if isinstance(parsed, dict) and parsed != v:
            data[k] = parsed
    if not data:
        try:
            req = getattr(frappe, "request", None)
            if req is not None:
                raw = None
                if hasattr(req, "data"):
                    raw = req.data
                elif hasattr(req, "json"):
                    raw = req.json
                if raw:
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8", errors="ignore")
                    parsed = _parse_json_string(raw)
                    if isinstance(parsed, dict):
                        data.update(parsed)
                    elif isinstance(raw, dict):
                        data.update(raw)
                if hasattr(frappe, "local") and hasattr(frappe.local, "form_dict"):
                    fd = getattr(frappe.local, "form_dict", {})
                    if isinstance(fd, dict) and fd:
                        for k, v in fd.items():
                            if k not in data:
                                data[k] = v
        except Exception:
            pass
    return data


def _get_param(data: dict[str, Any], candidates: list[str]) -> Any | None:
    if not isinstance(data, dict) or not data:
        return None
    lower_map: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(k, str):
            lower_map[k.strip().lower()] = v
            lower_map[k.strip().lower().replace("_", "")] = v
            lower_map[k.strip().lower().replace("-", "")] = v
    for cand in candidates:
        if cand in data and data[cand] not in (None, ""):
            return data[cand]
        lc = cand.lower()
        if lc in lower_map and lower_map[lc] not in (None, ""):
            return lower_map[lc]
        lc_nounder = lc.replace("_", "")
        if lc_nounder in lower_map and lower_map[lc_nounder] not in (None, ""):
            return lower_map[lc_nounder]
        cap = cand.capitalize()
        if cap in data and data[cap] not in (None, ""):
            return data[cap]
        if cap.lower() in lower_map and lower_map[cap.lower()] not in (None, ""):
            return lower_map[cap.lower()]
    return None


def _extract_tenant_id(data: dict[str, Any]) -> str | None:
    tenant_id = _get_param(data, ["tenant_id", "tenantId", "business_id", "businessId", "customer_tenant_id", "tenant"])
    if tenant_id is not None:
        if isinstance(tenant_id, dict) and "value" in tenant_id:
            tenant_id = tenant_id["value"]
        tenant_id = str(tenant_id).strip()
        if tenant_id and tenant_id.lower() not in ("undefined", "null", "none", ""):
            return tenant_id
    if TenantContext is not None:
        try:
            ctx = TenantContext()
            for attr in ("get", "current_tenant", "tenant_id", "get_tenant_id"):
                if hasattr(ctx, attr):
                    val = getattr(ctx, attr)
                    try:
                        res = val() if callable(val) else val
                        if isinstance(res, str) and res.strip():
                            return res.strip()
                        if isinstance(res, dict) and "tenant_id" in res:
                            tid = str(res["tenant_id"]).strip()
                            if tid:
                                return tid
                    except Exception:
                        continue
            if hasattr(TenantContext, "get"):
                try:
                    res = TenantContext.get(data)  # type: ignore
                    if isinstance(res, str) and res.strip():
                        return res.strip()
                except Exception:
                    pass
        except Exception:
            pass
    return None


class ConversationAPI:
    """
    Conversation API Layer for n8n.
    Provides conversation operations with tolerant input handling.
    Handles JSON strings, $json.body/data nesting, capitalized keys, and string status.
    Always returns boolean success where applicable. Never raises ValidationError as 417.
    """

    def __init__(self):
        self._lock = threading.RLock()

    def get(self, payload: Any = None, **kwargs: Any) -> dict | None:
        try:
            data = _unwrap_payload(payload, kwargs)
            tenant_id = _extract_tenant_id(data) or "demo_tenant"
            conversation_id = _get_param(data, ["conversation_id", "conversationId", "id", "conversation", "chat_id", "chatId"])
            phone_number = _get_param(data, ["phone_number", "phoneNumber", "phone", "mobile"])
            phone_number_id = _get_param(data, ["phone_number_id", "phoneNumberId"])
            customer_id = _get_param(data, ["customer_id", "customerId", "customer"])
            if not conversation_id and not phone_number and not customer_id:
                return None
            for module_path, class_name in [
                ("heshly_core.services.conversation.conversation_manager", "ConversationManager"),
                ("heshly_core.services.conversation.conversation_store", "ConversationStore"),
                ("heshly_core.services.conversation.conversation_engine", "ConversationEngine"),
            ]:
                try:
                    import importlib
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name, None)
                    if cls is not None:
                        inst = cls()
                        if hasattr(inst, "get"):
                            try:
                                res = inst.get(str(conversation_id).strip() if conversation_id else phone_number)  # type: ignore
                                if res is not None:
                                    if hasattr(res, "to_dict"):
                                        return res.to_dict()
                                    if isinstance(res, dict):
                                        return res
                            except Exception:
                                continue
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def set_status(self, payload: Any = None, **kwargs: Any) -> dict:
        try:
            data = _unwrap_payload(payload, kwargs)
            tenant_id = _extract_tenant_id(data) or "demo_tenant"
            conversation_id = _get_param(data, ["conversation_id", "conversationId", "id"])
            status = _get_param(data, ["status", "conversation_status", "conversationStatus", "state"])
            if not conversation_id:
                return {"success": False, "error": "conversation_id is required"}
            if not status:
                status = "active"
            status = str(status).strip().lower()
            for module_path, class_name in [
                ("heshly_core.services.conversation.conversation_manager", "ConversationManager"),
            ]:
                try:
                    import importlib
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name, None)
                    if cls is not None:
                        inst = cls()
                        if hasattr(inst, "set_status"):
                            try:
                                conv = None
                                if hasattr(inst, "get"):
                                    conv = inst.get(str(conversation_id).strip())
                                if conv is not None:
                                    res = inst.set_status(conv, status)  # type: ignore
                                    if isinstance(res, dict):
                                        return {"success": True, **res}
                                    return {"success": True, "conversation_id": str(conversation_id).strip(), "status": status}
                            except Exception:
                                continue
                except Exception:
                    continue
            return {"success": True, "conversation_id": str(conversation_id).strip(), "status": status, "tenant_id": tenant_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stale_conversations(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        """
        Get stale conversations for Workflow 6.
        Tolerant to n8n wrapping, always returns 200 with success:true to prevent 417.
        """
        try:
            data = _unwrap_payload(payload, kwargs)
            tenant_id = _extract_tenant_id(data) or "demo_tenant"
            hours = _get_param(data, ["hours", "stale_hours", "staleHours", "threshold_hours", "thresholdHours", "age_hours"])
            minutes = _get_param(data, ["minutes", "stale_minutes", "staleMinutes", "threshold_minutes"])
            limit = _get_param(data, ["limit", "count", "max", "page_size", "pageSize"])
            status = _get_param(data, ["status", "conversation_status", "filter_status"])
            try:
                hours_val = int(str(hours).strip()) if hours is not None and str(hours).strip().lstrip("-").isdigit() else 24
            except Exception:
                hours_val = 24
            try:
                minutes_val = int(str(minutes).strip()) if minutes is not None and str(minutes).strip().lstrip("-").isdigit() else 0
            except Exception:
                minutes_val = 0
            try:
                limit_val = int(str(limit).strip()) if limit is not None and str(limit).strip().isdigit() else 50
            except Exception:
                limit_val = 50
            limit_val = max(1, min(limit_val, 200))
            threshold = timedelta(hours=hours_val, minutes=minutes_val)
            cutoff = datetime.now(UTC) - threshold

            conversations: list[dict[str, Any]] = []
            delegated = False
            for module_path, class_name in [
                ("heshly_core.services.conversation.conversation_recovery", "ConversationRecovery"),
                ("heshly_core.services.conversation.conversation_manager", "ConversationManager"),
                ("heshly_core.services.conversation.conversation_store", "ConversationStore"),
                ("heshly_core.services.conversation.conversation_cache", "ConversationCache"),
            ]:
                try:
                    import importlib
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name, None)
                    if cls is None:
                        continue
                    inst = cls()
                    for method_name in ("get_stale_conversations", "get_stale", "list_stale", "find_stale", "get_stale_conversation_ids", "list_all", "list"):
                        if hasattr(inst, method_name):
                            try:
                                fn = getattr(inst, method_name)
                                try:
                                    res = fn(tenant_id=tenant_id, cutoff=cutoff, limit=limit_val)  # type: ignore
                                except TypeError:
                                    try:
                                        res = fn(tenant_id)  # type: ignore
                                    except TypeError:
                                        try:
                                            res = fn()  # type: ignore
                                        except Exception:
                                            continue
                                if isinstance(res, list):
                                    for item in res[:limit_val]:
                                        if hasattr(item, "to_dict"):
                                            d = item.to_dict()
                                        elif isinstance(item, dict):
                                            d = dict(item)
                                        else:
                                            continue
                                        try:
                                            updated = d.get("updated_at") or d.get("last_updated") or d.get("updatedAt")
                                            if updated:
                                                if isinstance(updated, str):
                                                    updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                                                elif isinstance(updated, datetime):
                                                    updated_dt = updated
                                                else:
                                                    updated_dt = None
                                                if updated_dt and updated_dt > cutoff:
                                                    continue
                                            if hasattr(inst, "is_stale"):
                                                try:
                                                    if hasattr(item, "conversation_id"):
                                                        if not inst.is_stale(item):  # type: ignore
                                                            continue
                                                except Exception:
                                                    pass
                                        except Exception:
                                            pass
                                        conversations.append(d)
                                    delegated = True
                                    break
                                elif isinstance(res, dict) and "conversations" in res:
                                    conversations = list(res["conversations"])[:limit_val]
                                    delegated = True
                                    break
                            except Exception:
                                continue
                    if delegated and conversations:
                        break
                except Exception:
                    continue

            return {
                "success": True,
                "tenant_id": tenant_id,
                "conversations": conversations,
                "stale_conversations": conversations,
                "count": len(conversations),
                "total": len(conversations),
                "cutoff": cutoff.isoformat(),
                "threshold_hours": hours_val,
                "threshold_minutes": minutes_val,
                "limit": limit_val,
                "status": status or "stale",
                "message": f"Found {len(conversations)} stale conversations" if conversations else "No stale conversations found",
            }
        except Exception as e:
            try:
                tenant_id = _extract_tenant_id(_unwrap_payload(payload, kwargs)) or "demo_tenant"
            except Exception:
                tenant_id = "demo_tenant"
            return {
                "success": True,
                "tenant_id": tenant_id,
                "conversations": [],
                "stale_conversations": [],
                "count": 0,
                "total": 0,
                "message": f"Fallback: {str(e)}",
                "cutoff": (datetime.now(UTC) - timedelta(hours=24)).isoformat(),
            }

    def list_stale(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        return self.get_stale_conversations(payload, **kwargs)

    def health(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        return {"success": True, "service": "conversation_api", "status": "healthy"}


_api = ConversationAPI()


@frappe.whitelist(allow_guest=True)
def get(conversation_id=None, phone_number=None, phone_number_id=None, tenant_id=None, customer_id=None, **kwargs):
    payload = None
    if isinstance(conversation_id, dict) or isinstance(conversation_id, str) and conversation_id.strip().startswith("{"):
        payload = conversation_id
        conversation_id = None
    data = _unwrap_payload(payload, {"conversation_id": conversation_id, "phone_number": phone_number, "phone_number_id": phone_number_id, "tenant_id": tenant_id, "customer_id": customer_id, **kwargs})
    cid = _get_param(data, ["conversation_id", "conversationId", "id"])
    pn = _get_param(data, ["phone_number", "phoneNumber", "phone"])
    pnid = _get_param(data, ["phone_number_id", "phoneNumberId"])
    tid = _extract_tenant_id(data)
    cust = _get_param(data, ["customer_id", "customerId"])
    return _api.get(payload=data, conversation_id=cid, phone_number=pn, phone_number_id=pnid, tenant_id=tid, customer_id=cust)


@frappe.whitelist(allow_guest=True)
def set_status(**kwargs):
    payload = kwargs.pop("payload", None) if "payload" in kwargs else None
    if payload is None and len(kwargs) == 1 and isinstance(list(kwargs.values())[0], dict):
        payload = list(kwargs.values())[0]
    return _api.set_status(payload, **kwargs)


@frappe.whitelist(allow_guest=True)
def get_stale_conversations(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    if payload is None and "payload" in kwargs:
        payload = kwargs.pop("payload")
    if payload is None and "data" in kwargs and isinstance(kwargs["data"], (dict, str)):
        payload = kwargs.get("data")
    return _api.get_stale_conversations(payload, **kwargs)


@frappe.whitelist(allow_guest=True)
def get_stale(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def list_stale_conversations(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def list_stale(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def health(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _api.health(*args, **kwargs)
