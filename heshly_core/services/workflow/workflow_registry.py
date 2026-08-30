from __future__ import annotations

import json
import threading
from typing import Any

# Maps n8n workflowId (UUID) -> heshly industry/template
# Fixes "Workflow does not exist" when n8n Execute Workflow node references deleted/missing workflow

_DEFAULT_REGISTRY: dict[str, dict[str, str]] = {
    # WF3/2 - the missing workflow from error
    "37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd": {
        "industry": "dental",
        "name": "WF3/2 - Dental Booking Child",
        "template_id": "dental",
    },
}

class WorkflowRegistry:
    """
    Registry for n8n workflowId -> heshly template mapping.
    Thread-safe, tolerant to JSON strings and n8n wrapping.
    Auto-creates missing WF3/2 entry.
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
            return dict(self._map[nid]) if nid in self._map else None

    def exists(self, workflow_id: Any) -> bool:
        return self.get(workflow_id) is not None

    def resolve_industry(self, workflow_id: Any) -> str | None:
        entry = self.get(workflow_id)
        return entry["industry"] if entry else None

    def get_workflow_id_for_industry(self, industry: str) -> str | None:
        if not isinstance(industry, str) or not industry.strip():
            return None
        with self._lock:
            return self._reverse.get(industry.strip().lower())

    def list_all(self) -> dict[str, dict[str, str]]:
        with self._lock:
            return {k: dict(v) for k, v in self._map.items()}

    def ensure_wf3(self) -> dict[str, str]:
        # Ensure WF3/2 exists - idempotent
        wf_id = "37bdbe49-2f7c-44ff-9132-4b2c9e3d33fd"
        if not self.exists(wf_id):
            self.register(wf_id, "dental", "WF3/2 - Dental Booking Child", "dental")
        return self.get(wf_id)  # type: ignore

# Singleton
_registry = WorkflowRegistry()

def get_registry() -> WorkflowRegistry:
    return _registry
