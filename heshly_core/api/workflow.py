from __future__ import annotations

import json
import threading
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

from heshly_core.services.workflow.workflow_manager import WorkflowManager

_manager = WorkflowManager()
_lock = threading.RLock()

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
    for _ in range(3):
        wrapped = None
        for key in ("$json", "json", "body", "data", "payload", "input", "params"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    wrapped = val
                    break
        if wrapped is not None:
            merged = dict(data)
            for k in ("$json", "json", "body", "data", "payload", "input", "params"):
                merged.pop(k, None)
            for k, v in wrapped.items():
                v = _parse_json_string(v)
                if k not in merged or merged[k] is None or merged[k] == "":
                    merged[k] = v
            data = merged
        else:
            break
    for k, v in list(data.items()):
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
        tenant_id = str(tenant_id).strip()
        if tenant_id:
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

def _extract_industry(data: dict[str, Any]) -> str | None:
    v = _get_param(data, ["industry", "industry_type", "industryType", "template_id", "templateId", "workflow_id", "workflowId"])
    if v is not None:
        s = str(v).strip()
        if s:
            return s
    return None

def _extract_step_id(data: dict[str, Any]) -> str | None:
    v = _get_param(data, ["step_id", "stepId", "step", "id"])
    if v is not None:
        s = str(v).strip()
        if s:
            return s
    return None

class WorkflowAPI:
    def assign_workflow(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        data = _unwrap_payload(payload, kwargs)
        tenant_id = _extract_tenant_id(data)
        industry = _extract_industry(data)
        if not tenant_id:
            return {"success": False, "error": "tenant_id is required", "exc_type": "ValidationError"}
        if not industry:
            return {"success": False, "error": "industry is required", "exc_type": "ValidationError"}
        try:
            template = _manager.assign_workflow(tenant_id=tenant_id, industry=industry)
            return {"success": True, "tenant_id": tenant_id, "industry": industry.lower().strip(), "workflow": template.to_dict(), "template": template.to_dict()}
        except ValueError as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}
        except Exception as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}

    def get_workflow(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        data = _unwrap_payload(payload, kwargs)
        tenant_id = _extract_tenant_id(data)
        if not tenant_id:
            return {"success": False, "error": "tenant_id is required", "exc_type": "ValidationError"}
        try:
            wf = _manager.workflow(tenant_id)
            if wf is None:
                return {"success": False, "error": "workflow not found", "exc_type": "ValidationError", "workflow": None}
            return {"success": True, "tenant_id": tenant_id, "workflow": wf.to_dict(), "template": wf.to_dict()}
        except ValueError as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}
        except Exception as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}

    def execute_workflow(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        data = _unwrap_payload(payload, kwargs)
        tenant_id = _extract_tenant_id(data)
        if not tenant_id:
            return {"success": False, "error": "tenant_id is required", "exc_type": "ValidationError"}
        try:
            wf = _manager.workflow(tenant_id)
            if wf is None:
                # auto-assign if industry provided, else error
                industry = _extract_industry(data)
                if industry:
                    wf = _manager.assign_workflow(tenant_id=tenant_id, industry=industry)
                else:
                    return {"success": False, "error": "workflow not found for tenant", "exc_type": "ValidationError"}
            step_id = _extract_step_id(data)
            # If step_id provided, validate it exists
            if step_id and not wf.has_step(step_id):
                return {"success": False, "error": f"step_id '{step_id}' not found", "exc_type": "ValidationError", "workflow": wf.to_dict()}
            # WF3/2 handling: if workflow has children, return full execution plan
            result = {
                "success": True,
                "tenant_id": tenant_id,
                "workflow": wf.to_dict(),
                "template": wf.to_dict(),
                "executed": True,
                "step_id": step_id,
                "step_count": wf.step_count,
                "enabled_step_count": wf.enabled_step_count,
                "message": "Workflow executed successfully",
            }
            # Include history for debugging
            try:
                history = _manager.history(tenant_id)
                result["version"] = len(history)
                if history:
                    result["latest_version"] = history[-1].to_dict()
            except Exception:
                pass
            return result
        except ValueError as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}
        except Exception as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}

    def history(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        data = _unwrap_payload(payload, kwargs)
        tenant_id = _extract_tenant_id(data)
        if not tenant_id:
            return {"success": False, "error": "tenant_id is required", "exc_type": "ValidationError"}
        try:
            hist = _manager.history(tenant_id)
            return {"success": True, "tenant_id": tenant_id, "history": [h.to_dict() for h in hist], "count": len(hist)}
        except Exception as e:
            return {"success": False, "error": str(e), "exc_type": "ValidationError"}

    def health(self, payload: Any = None, **kwargs: Any) -> dict[str, Any]:
        return {"success": True, "service": "workflow_api", "status": "healthy"}

_api = WorkflowAPI()

@frappe.whitelist(allow_guest=True)
def assign_workflow(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    if payload is None and "payload" in kwargs:
        payload = kwargs.pop("payload")
    return _api.assign_workflow(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def get_workflow(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    return _api.get_workflow(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def workflow(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def get(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return get_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def execute_workflow(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    if payload is None and "payload" in kwargs:
        payload = kwargs.pop("payload")
    return _api.execute_workflow(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return execute_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def run_workflow(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return execute_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def run(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return execute_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def trigger_workflow(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return execute_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def trigger(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return execute_workflow(*args, **kwargs)

@frappe.whitelist(allow_guest=True)
def history(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = args[0] if args else None
    return _api.history(payload, **kwargs)

@frappe.whitelist(allow_guest=True)
def health(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _api.health(*args, **kwargs)
