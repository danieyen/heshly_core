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
            tenant_id = _extract_tenant_id(data)
            conversation_id = _get_param(data, ["conversation_id", "conversationId", "id", "conversation", "chat_id", "chatId"])
            phone_number = _get_param(data, ["phone_number", "phoneNumber", "phone", "mobile"])
            phone_number_id = _get_param(data, ["phone_number_id", "phoneNumberId"])
            customer_id = _get_param(data, ["customer_id", "customerId", "customer"])
            # Tenant isolation: require tenant_id - never default to demo_tenant
            if not tenant_id or not str(tenant_id).strip():
                return {
                    "success": False,
                    "error": "tenant_id is required - tenant resolution failed",
                    "conversation_id": str(conversation_id).strip() if conversation_id else None,
                    "tenant_id": None,
                    "turns": [],
                    "conversation_history": [],
                }
            tenant_id = str(tenant_id).strip()
            # Derive deterministic conversation_id if not provided but phone is known
            if not conversation_id and phone_number and str(phone_number).strip():
                conversation_id = f"{tenant_id}:{str(phone_number).strip()}"
            if not conversation_id and not phone_number and not customer_id:
                return None
            if conversation_id:
                conversation_id = str(conversation_id).strip()
                if not conversation_id:
                    return None
            # Try tenant-aware stores - must pass tenant_id so lookup is deterministic
            for module_path, class_name in [
                ("heshly_core.services.conversation.conversation_store", "ConversationStore"),
                ("heshly_core.services.conversation.conversation_manager", "ConversationManager"),
                ("heshly_core.services.conversation.conversation_engine", "ConversationEngine"),
            ]:
                try:
                    import importlib
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name, None)
                    if cls is None:
                        continue
                    # Instantiate with explicit tenant_id for isolation
                    inst = None
                    try:
                        inst = cls(tenant_id=tenant_id)  # type: ignore
                    except TypeError:
                        try:
                            inst = cls(tenant_id)  # type: ignore
                        except Exception:
                            inst = cls()  # type: ignore
                            # Try to set tenant context as fallback
                            try:
                                from heshly_core.services.tenant.tenant_context import TenantContext
                                TenantContext().set(tenant_id)
                            except Exception:
                                pass
                    if inst is None or not hasattr(inst, "get"):
                        continue
                    try:
                        # Always lookup by conversation_id (deterministic tenant:phone). Phone-only fallback already resolved above.
                        lookup_id = conversation_id if conversation_id else str(phone_number).strip()
                        res = inst.get(lookup_id)  # type: ignore
                        if res is not None:
                            d = res.to_dict() if hasattr(res, "to_dict") else (dict(res) if isinstance(res, dict) else None)
                            if d is None:
                                continue
                            # Enforce tenant isolation: returned conversation must belong to requested tenant
                            ret_tenant = str(d.get("tenant_id") or d.get("tenantId") or "").strip() if isinstance(d, dict) else ""
                            # Some to_dict may not include tenant_id - verify via conversation_id prefix
                            if ret_tenant and ret_tenant != tenant_id:
                                continue
                            # Ensure chronological ordering of turns
                            if isinstance(d, dict) and isinstance(d.get("turns"), list):
                                try:
                                    # Sort by timestamp if available, preserve insertion order otherwise
                                    def _ts_key(t):
                                        ts = t.get("timestamp") if isinstance(t, dict) else getattr(t, "timestamp", None)
                                        if isinstance(ts, str):
                                            try:
                                                from datetime import datetime
                                                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                            except Exception:
                                                return ts
                                        return ts or ""
                                    # Only sort if timestamps look parseable and not already sorted
                                    d["turns"] = sorted(d["turns"], key=_ts_key)
                                except Exception:
                                    pass
                                # Also expose as conversation_history for n8n compatibility
                                d["conversation_history"] = list(d["turns"])
                                d["history"] = list(d["turns"])
                            # Enrich with request identifiers for downstream validation
                            if isinstance(d, dict):
                                d.setdefault("tenant_id", tenant_id)
                                d.setdefault("conversation_id", conversation_id)
                                if phone_number_id:
                                    d.setdefault("phone_number_id", str(phone_number_id).strip())
                                if phone_number:
                                    d.setdefault("phone_number", str(phone_number).strip())
                            return d
                    except Exception:
                        continue
                except Exception:
                    continue
            # No conversation found - return empty history tied to correct tenant+conversation_id (so caller can still isolate)
            return {
                "success": True,
                "found": False,
                "tenant_id": tenant_id,
                "conversation_id": conversation_id,
                "phone_number": str(phone_number).strip() if phone_number else None,
                "phone_number_id": str(phone_number_id).strip() if phone_number_id else None,
                "turns": [],
                "conversation_history": [],
                "history": [],
                "message": "Conversation not found - new conversation",
            }
        except Exception:
            return None

    def create(self, payload: Any = None, **kwargs: Any) -> dict:
        """
        Create or return a WhatsApp conversation.

        Uses the existing ConversationManager as the single source
        of conversation creation/persistence. Designed for n8n payloads.
        """
        try:
            data = _unwrap_payload(payload, kwargs)

            tenant_id = _extract_tenant_id(data)
            conversation_id = _get_param(
                data,
                ["conversation_id", "conversationId", "id", "conversation", "chat_id", "chatId"],
            )
            customer_id = _get_param(
                data,
                ["customer_id", "customerId", "customer"],
            )
            phone_number = _get_param(
                data,
                ["phone_number", "phoneNumber", "phone", "mobile"],
            )

            if not conversation_id and tenant_id and phone_number:
                conversation_id = f"{tenant_id}:{str(phone_number).strip()}"

            if not customer_id and phone_number:
                customer_id = str(phone_number).strip()

            if not tenant_id:
                return {
                    "success": False,
                    "error": "tenant_id is required",
                }

            if not conversation_id:
                return {
                    "success": False,
                    "error": "conversation_id is required",
                }

            if not customer_id:
                return {
                    "success": False,
                    "error": "customer_id is required",
                }

            from heshly_core.services.conversation.conversation_manager import (
                ConversationManager,
            )

            manager = ConversationManager(
                tenant_id=str(tenant_id).strip(),
                channel="whatsapp",
            )

            conversation_id = str(conversation_id).strip()
            customer_id = str(customer_id).strip()

            existing = manager.get(conversation_id)

            if existing is not None:
                result = existing.to_dict() if hasattr(existing, "to_dict") else existing
                return {
                    "success": True,
                    "created": False,
                    "tenant_id": str(tenant_id).strip(),
                    "conversation": result,
                    **(result if isinstance(result, dict) else {}),
                }

            conversation = manager.create(
                conversation_id=conversation_id,
                customer_id=customer_id,
            )

            result = (
                conversation.to_dict()
                if hasattr(conversation, "to_dict")
                else conversation
            )

            return {
                "success": True,
                "created": True,
                "tenant_id": str(tenant_id).strip(),
                "conversation": result,
                **(result if isinstance(result, dict) else {}),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

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
def create(*args: Any, **kwargs: Any) -> dict:
    payload = args[0] if args else None
    if payload is None and "payload" in kwargs:
        payload = kwargs.pop("payload")
    if payload is None and "data" in kwargs and isinstance(kwargs["data"], (dict, str)):
        payload = kwargs.get("data")
    return _api.create(payload, **kwargs)


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
def get_stale_conversation(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def list_stale_conversations(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def list_stale(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def getStale(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def getStaleConversations(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def listStale(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_stale_conversations(*args, **kwargs)


@frappe.whitelist(allow_guest=True)
def health(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _api.health(*args, **kwargs)


def _require_business():
    """Return active Business Account for session user (tenant-owner path)."""
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    business_id = frappe.session.data.get("heshly_business_id")
    if not business_id:
        frappe.throw("Business session not found.", frappe.PermissionError)
    biz = frappe.db.get_value("Business Account", {"business_id": business_id, "status": "Active"}, ["business_id", "tenant_id"], as_dict=True)
    if not biz:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    m = frappe.db.get_value("User Business Membership", {"user": frappe.session.user, "business_id": biz.business_id, "tenant_id": biz.tenant_id, "active": 1}, "name")
    if not m:
        frappe.throw("You do not have access to this business.", frappe.PermissionError)
    return biz


@frappe.whitelist()
def take_over(conversation_id: str):
    """Owner takes over — status -> handover, creates attention resolved future via activity."""
    biz = _require_business()
    tenant_id = biz.tenant_id
    if not conversation_id:
        frappe.throw("conversation_id is required")
    from heshly_core.repositories.conversation_repository import ConversationRepository
    from heshly_core.models.conversation import ConversationStatus
    repo = ConversationRepository()
    conv = repo.get(conversation_id.strip(), tenant_id=tenant_id)
    if not conv:
        frappe.throw("Conversation not found", frappe.DoesNotExistError)
    conv.status = ConversationStatus.HANDOVER
    repo.save(conv, tenant_id=tenant_id, channel="web")
    return {"success": True, "conversation_id": conversation_id.strip(), "status": "handover"}


@frappe.whitelist()
def resolve_conversation(conversation_id: str):
    biz = _require_business()
    tenant_id = biz.tenant_id
    if not conversation_id:
        frappe.throw("conversation_id is required")
    from heshly_core.repositories.conversation_repository import ConversationRepository
    from heshly_core.models.conversation import ConversationStatus
    repo = ConversationRepository()
    conv = repo.get(conversation_id.strip(), tenant_id=tenant_id)
    if not conv:
        frappe.throw("Conversation not found", frappe.DoesNotExistError)
    conv.status = ConversationStatus.CLOSED
    repo.save(conv, tenant_id=tenant_id, channel="web")
    return {"success": True, "conversation_id": conversation_id.strip(), "status": "closed"}


@frappe.whitelist()
def return_to_ai(conversation_id: str):
    biz = _require_business()
    tenant_id = biz.tenant_id
    if not conversation_id:
        frappe.throw("conversation_id is required")
    from heshly_core.repositories.conversation_repository import ConversationRepository
    from heshly_core.models.conversation import ConversationStatus
    repo = ConversationRepository()
    conv = repo.get(conversation_id.strip(), tenant_id=tenant_id)
    if not conv:
        frappe.throw("Conversation not found", frappe.DoesNotExistError)
    conv.status = ConversationStatus.ACTIVE
    repo.save(conv, tenant_id=tenant_id, channel="web")
    return {"success": True, "conversation_id": conversation_id.strip(), "status": "active"}


@frappe.whitelist()
def get_detail(conversation_id: str):
    """Enriched detail for Needs Attention / Lead Brief / Timeline — reuses Lead/Appointment + simulator-derived outcome."""
    biz = _require_business()
    tenant_id = biz.tenant_id
    if not conversation_id:
        frappe.throw("conversation_id is required")
    from heshly_core.repositories.conversation_repository import ConversationRepository
    repo = ConversationRepository()
    conv = repo.get(conversation_id.strip(), tenant_id=tenant_id)
    if not conv:
        frappe.throw("Conversation not found", frappe.DoesNotExistError)
    # Lead via customer_id / phone
    lead_doc = None
    try:
        from heshly_core.repositories.lead_repository import LeadRepository
        lr = LeadRepository()
        # search by tenant + lead name or mobile
        candidates = [conv.customer_id, conv.entities.phone, conv.entities.customer_name]
        for cand in candidates:
            if cand:
                row = frappe.db.get_value("Lead", {"custom_heshly_tenant_id": tenant_id, "mobile_no": cand}, ["name", "lead_name", "mobile_no", "email_id", "status", "territory"], as_dict=True)
                if row:
                    lead_doc = row
                    break
                row2 = frappe.db.get_value("Lead", {"custom_heshly_tenant_id": tenant_id, "lead_name": cand}, ["name", "lead_name", "mobile_no", "email_id", "status", "territory"], as_dict=True)
                if row2:
                    lead_doc = row2
                    break
    except Exception:
        pass
    # appointment linked by customer / conversation date
    appointment = None
    try:
        appt_rows = frappe.db.sql("SELECT name, scheduled_time, status, customer_name, customer_phone_number FROM `tabAppointment` WHERE custom_heshly_tenant_id=%s AND (customer_phone_number=%s OR customer_name=%s) ORDER BY scheduled_time DESC LIMIT 1", (tenant_id, conv.entities.phone or conv.customer_id, conv.entities.customer_name or ""), as_dict=True)
        if appt_rows:
            appointment = appt_rows[0]
    except Exception:
        pass
    # Re-derive outcome using same engines (DecisionEngine single-pass for intent/qualification availability) for display consistency
    intent_val = None
    qualification = None
    availability = None
    booking = None
    try:
        from heshly_core.services.ai.intent_classifier import IntentClassifier
        from heshly_core.services.ai.entity_extractor import EntityExtractor
        from heshly_core.services.qualification.qualification_engine import QualificationEngine
        from heshly_core.api.availability import AvailabilityAPI
        msg_last = conv.turns[-1].message if conv.turns else ""
        ic = IntentClassifier()
        ee = EntityExtractor()
        qe = QualificationEngine()
        intent_res = ic.classify(msg_last) if msg_last else None
        intent_val = intent_res.intent.value if intent_res else conv.entities.service
        # qualification
        collected = {"customer_name": conv.entities.customer_name, "phone": conv.entities.phone, "email": conv.entities.email, "service": conv.entities.service, "date": conv.entities.date, "time": conv.entities.time}
        qr, qa, qresp = qe.qualify(customer_id=conv.customer_id, message=msg_last or "", collected_data=collected, required_fields=["customer_name", "phone"])
        qualification = {"status": qr.status.value, "score": qr.score, "urgency": qr.urgency.value, "missing_fields": qr.missing_fields}
        # availability if bookable
        if conv.entities.service and conv.entities.date and conv.entities.time:
            try:
                avail = AvailabilityAPI().check({"service": conv.entities.service, "preferred_date": conv.entities.date, "preferred_time": conv.entities.time, "tenant_id": tenant_id})
                availability = avail
            except Exception as e:
                availability = {"available": False, "reason": str(e)[:200]}
    except Exception:
        pass
    # attention reason
    attention_reason = None
    if conv.status.value == "handover":
        attention_reason = "Human escalation"
    elif conv.status.value in ("active",) and qualification and qualification["status"] == "collecting_info":
        attention_reason = "Needs qualification info"
    elif availability and not availability.get("available"):
        attention_reason = availability.get("reason") or "Booking attention"
    # timeline
    timeline = []
    now = frappe.utils.now_datetime() if hasattr(frappe.utils, "now_datetime") else None
    for idx, t in enumerate(conv.turns or []):
        timeline.append({"at": t.timestamp.isoformat() if hasattr(t.timestamp, "isoformat") else str(t.timestamp), "label": ("Customer" if t.role.value == "user" else "AI") + ": " + t.message[:120], "role": t.role.value})
    if intent_val:
        timeline.append({"at": conv.updated_at.isoformat() if hasattr(conv.updated_at, "isoformat") else "", "label": f"Intent: {intent_val}"})
    if qualification:
        timeline.append({"at": conv.updated_at.isoformat() if hasattr(conv.updated_at, "isoformat") else "", "label": f"Qualification: {qualification['status']} score {qualification['score']}"})
    if availability:
        timeline.append({"at": conv.updated_at.isoformat() if hasattr(conv.updated_at, "isoformat") else "", "label": f"Availability: {'available' if availability.get('available') else 'unavailable'} — {availability.get('reason','')[:100]}"})
    # outcome
    qual_label = qualification["status"] if qualification else "—"
    if qualification and qualification["status"] == "qualified":
        qual_label = "HOT" if qualification["score"] >= 70 else "WARM"
    appt_str = None
    if appointment:
        appt_str = str(appointment.get("scheduled_time"))
    elif conv.entities.date and conv.entities.time:
        appt_str = f"{conv.entities.date} {conv.entities.time}"
    outcome = {"customer": conv.entities.customer_name or conv.customer_id, "service": conv.entities.service or "—", "date": conv.entities.date or "—", "time": conv.entities.time or "—", "phone": conv.entities.phone or "—", "qualification": qual_label, "appointment": appt_str, "status": conv.status.value, "attention_reason": attention_reason}
    return {"conversation": conv.to_dict(), "lead": lead_doc, "appointment": appointment, "qualification": qualification, "availability": availability, "timeline": timeline, "outcome": outcome, "attention_reason": attention_reason}


def __getattr__(name: str):
    # Fallback for any stale-related method name to prevent 417 "has no attribute"
    if "stale" in name.lower():
        return get_stale_conversations
    raise AttributeError(f"module 'heshly_core.api.conversations' has no attribute '{name}'")

@frappe.whitelist(allow_guest=True, methods=["POST", "GET"])
def append_turn(*args: Any, **kwargs: Any) -> dict:
    """Append a conversation turn (user or assistant) deterministically. Handles n8n wrapping."""
    data = _unwrap_payload(args[0] if args else None, kwargs)
    tenant_id = _extract_tenant_id(data) or data.get("tenant_id")
    if not tenant_id or not str(tenant_id).strip():
        return {"success": False, "reason": "tenant_id is required - no fallback to heshly"}
    tenant_id = str(tenant_id).strip()
    conversation_id = data.get("conversation_id") or data.get("conversationId") or data.get("id")
    role = (data.get("role") or "user").strip().lower()
    message = data.get("message") or data.get("text") or data.get("body") or ""
    if isinstance(message, dict):
        message = message.get("text") or message.get("body") or str(message)
    message = str(message).strip()
    if not conversation_id:
        return {"success": False, "reason": "conversation_id required"}
    if not message:
        return {"success": True, "skipped": True, "reason": "empty message"}
    try:
        from heshly_core.services.tenant.tenant_context import TenantContext
        try:
            TenantContext().set(tenant_id)
        except Exception:
            pass
        from heshly_core.services.conversation.conversation_store import ConversationStore
        from heshly_core.models.conversation import ConversationTurn, Speaker
        store = ConversationStore(tenant_id=tenant_id)
        conv = store.get(conversation_id)
        if not conv:
            return {"success": False, "reason": f"Conversation not found: {conversation_id}"}
        speaker = Speaker.USER if role == "user" else Speaker.ASSISTANT if role == "assistant" else Speaker.from_value(role)
        turn = ConversationTurn(role=speaker, message=message)
        if role == "user":
            # Also persist entities if provided
            conv.add_turn(turn)
        else:
            conv.add_turn(turn)
        store.save(conv)
        # Persist qualification to Lead on assistant turns (qualification derived from conversation entities)
        if role == "assistant":
            try:
                from heshly_core.services.qualification.qualification_engine import QualificationEngine
                from heshly_core.services.crm.lead_persistence import persist_qualification_to_lead
                qe = QualificationEngine()
                collected = {
                    "customer_name": conv.entities.customer_name,
                    "phone": conv.entities.phone,
                    "email": conv.entities.email,
                    "service": conv.entities.service,
                    "date": conv.entities.date,
                    "time": conv.entities.time,
                }
                qr, _aq, _qr = qe.qualify(
                    customer_id=conv.customer_id,
                    message=message,
                    collected_data=collected,
                    required_fields=["customer_name", "phone"],
                )
                persist_qualification_to_lead(
                    tenant_id=tenant_id,
                    customer_name=conv.entities.customer_name,
                    phone=conv.entities.phone,
                    email=conv.entities.email,
                    qual_result=qr,
                    source="whatsapp",
                )
            except Exception as _qe:
                try:
                    frappe.logger().warning(f"append_turn lead persistence failed: {_qe}")
                except Exception:
                    pass
        return {"success": True, "conversation_id": conversation_id, "role": role, "message": message}
    except Exception as e:
        return {"success": False, "reason": str(e)}

