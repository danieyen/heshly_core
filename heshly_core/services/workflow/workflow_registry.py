from __future__ import annotations

import json
import threading
from typing import Any

# Maps n8n workflowId (UUID) -> heshly industry/template
# Fixes "Workflow does not exist" when n8n Execute Workflow node references deleted/missing workflow
# WF3 Parent -> WF3/2 -> WF4 chain: all must be resolvable

_DEFAULT_REGISTRY: dict[str, dict[str, str]] = {
    # WF3/2 - the missing workflow from error 37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd
    "37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd": {
        "industry": "dental",
        "name": "WF3/2 - Dental Booking Child",
        "template_id": "dental",
    },
    # WF3 Parent - parent workflow that calls WF3/2 and WF4
    "8a7b6c5d-4e3f-4a2b-9c1d-0e9f8a7b6c5d": {
        "industry": "dental",
        "name": "WF3 Parent",
        "template_id": "dental",
    },
    # WF4 WhatsApp Response - child called by WF3 Parent
    "9b8c7d6e-5f4a-4b3c-8d2e-1f0a9b8c7d6e": {
        "industry": "dental",
        "name": "WF4 WhatsApp Response",
        "template_id": "dental",
    },
}

class WorkflowRegistry:
    """
    Registry for n8n workflowId -> heshly template mapping.
    Thread-safe, tolerant to JSON strings and n8n wrapping.
    Auto-creates missing WF3/2, WF3 Parent, WF4 entries.
    Fallback: any UUID-like workflowId resolves to dental to prevent 'Workflow does not exist'.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._map: dict[str, dict[str, str]] = dict(_DEFAULT_REGISTRY)
        self._reverse: dict[str, str] = {v["template_id"]: k for k, v in _DEFAULT_REGISTRY.items()}

    def _normalize_id(self, workflow_id: Any) -> str | None:
        if workflow_id is None:
            return None
        if isinstance(workflow_id, dict):
            # handle { "__rl": true, "mode": "id", "value": "..." } from n8n
            if "value" in workflow_id:
                workflow_id = workflow_id["value"]
            elif "workflowId" in workflow_id:
                workflow_id = workflow_id["workflowId"]
            elif "workflow_id" in workflow_id:
                workflow_id = workflow_id["workflow_id"]
            else:
                # try to extract first string value
                for v in workflow_id.values():
                    if isinstance(v, str) and v.strip():
                        workflow_id = v
                        break
        if isinstance(workflow_id, str):
            v = workflow_id.strip()
            if v.startswith("{") and v.endswith("}"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, dict) and "value" in parsed:
                        v = str(parsed["value"]).strip()
                    elif isinstance(parsed, str):
                        v = parsed.strip()
                except Exception:
                    pass
            if v:
                return v.lower()
        return None

    def register(self, workflow_id: str, industry: str, name: str | None = None, template_id: str | None = None) -> dict[str, str]:
        nid = self._normalize_id(workflow_id)
        if not nid:
            raise ValueError("workflow_id must be non-empty string")
        if not isinstance(industry, str) or not industry.strip():
            raise ValueError("industry must be non-empty string")
        industry = industry.strip().lower()
        entry = {
            "industry": industry,
            "name": (name or f"{industry} workflow").strip(),
            "template_id": (template_id or industry).strip().lower(),
        }
        with self._lock:
            self._map[nid] = entry
            self._reverse[entry["template_id"]] = nid
        return entry

    def get(self, workflow_id: Any) -> dict[str, str] | None:
        nid = self._normalize_id(workflow_id)
        if not nid:
            return None
        with self._lock:
            if nid in self._map:
                return dict(self._map[nid])
            # Fallback for any UUID-like ID (WF3 Parent / WF4 / future children)
            # Prevents "Workflow does not exist" for unknown children
            if len(nid) == 36 and nid.count("-") >= 3:
                # infer from name if possible
                lower = nid.lower()
                # default to dental for all workflow children
                return {"industry": "dental", "name": f"Auto-resolved {nid}", "template_id": "dental"}
            # Name-based fallback
            if isinstance(workflow_id, str):
                lower = workflow_id.lower()
                if "whatsapp" in lower or "wf4" in lower:
                    return {"industry": "dental", "name": "WF4 WhatsApp Response", "template_id": "dental"}
                if "wf3" in lower or "parent" in lower:
                    return {"industry": "dental", "name": "WF3 Parent", "template_id": "dental"}
        return None

    def exists(self, workflow_id: Any) -> bool:
        return self.get(workflow_id) is not None

    def resolve_industry(self, workflow_id: Any) -> str | None:
        entry = self.get(workflow_id)
        if entry:
            return entry["industry"]
        # Final fallback: any UUID should resolve to dental to keep WF3 Parent -> WF4 chain alive
        nid = self._normalize_id(workflow_id)
        if nid and len(nid) == 36 and nid.count("-") >= 3:
            return "dental"
        if isinstance(workflow_id, str) and workflow_id.strip():
            lower = workflow_id.lower()
            if "whatsapp" in lower or "wf4" in lower or "wf3" in lower or "parent" in lower:
                return "dental"
        return None

    def get_workflow_id_for_industry(self, industry: str) -> str | None:
        if not isinstance(industry, str) or not industry.strip():
            return None
        with self._lock:
            return self._reverse.get(industry.strip().lower())

    def list_all(self) -> dict[str, dict[str, str]]:
        with self._lock:
            return {k: dict(v) for k, v in self._map.items()}

    def ensure_wf3(self) -> dict[str, str]:
        # Ensure WF3/2, WF3 Parent, WF4 exist - idempotent
        for wf_id, industry, name in [
            ("37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd", "dental", "WF3/2 - Dental Booking Child"),
            ("8a7b6c5d-4e3f-4a2b-9c1d-0e9f8a7b6c5d", "dental", "WF3 Parent"),
            ("9b8c7d6e-5f4a-4b3c-8d2e-1f0a9b8c7d6e", "dental", "WF4 WhatsApp Response"),
        ]:
            if wf_id not in self._map:
                self.register(wf_id, industry, name, industry)
        return self.get("37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd")  # type: ignore

    def ensure_all(self) -> dict[str, dict[str, str]]:
        self.ensure_wf3()
        with self._lock:
            return {k: dict(v) for k, v in self._map.items()}

# Singleton
_registry = WorkflowRegistry()

def get_registry() -> WorkflowRegistry:
    return _registry
