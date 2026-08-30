from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from heshly_core.models.workflow_template import (
    WorkflowTemplate,
)
from heshly_core.models.workflow_version import (
    WorkflowVersion,
)
from heshly_core.repositories.workflow_version_repository import (
    WorkflowVersionRepository,
)

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

def _unwrap(data: Any) -> dict[str, Any]:
    if isinstance(data, str):
        parsed = _parse_json_string(data)
        if isinstance(parsed, dict):
            return parsed
        return {}
    if isinstance(data, dict):
        for key in ("$json", "json", "body", "data", "payload"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    merged = dict(data)
                    merged.pop(key, None)
                    for k, v in val.items():
                        if k not in merged or merged[k] in (None, ""):
                            merged[k] = v
                    return merged
        return data
    return {}

def _get(data: dict[str, Any], *candidates: str) -> Any | None:
    if not isinstance(data, dict):
        return None
    lower = {str(k).lower().replace("_","").replace("-",""): v for k, v in data.items() if isinstance(k, str)}
    for c in candidates:
        if c in data and data[c] not in (None, ""):
            return data[c]
        lc = c.lower().replace("_","").replace("-","")
        if lc in lower and lower[lc] not in (None, ""):
            return lower[lc]
    return None


class WorkflowVersionManager:
    """
    Workflow Version Manager.
    Tolerant to n8n wrapping.
    """

    def __init__(self):

        self.repository = (
            WorkflowVersionRepository()
        )

    def _validate_tenant_id(self, tenant_id: Any) -> str:
        if isinstance(tenant_id, dict):
            tenant_id = _get(_unwrap(tenant_id), "tenant_id", "tenantId", "business_id") or tenant_id
        if isinstance(tenant_id, str):
            parsed = _parse_json_string(tenant_id)
            if isinstance(parsed, dict):
                tid = _get(parsed, "tenant_id", "tenantId")
                if tid is not None:
                    tenant_id = tid
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return tenant_id.strip()

    def _validate_workflow(self, workflow: Any) -> WorkflowTemplate:
        if isinstance(workflow, dict):
            workflow = WorkflowTemplate.from_dict(workflow)
        if isinstance(workflow, str):
            workflow = WorkflowTemplate.from_dict(_parse_json_string(workflow))
        if not isinstance(workflow, WorkflowTemplate):
            raise ValueError("workflow must be a WorkflowTemplate instance")
        if not workflow.template_id.strip():
            raise ValueError("workflow.template_id must be non-empty")
        return workflow

    def create_version(
        self,
        tenant_id: str | dict | Any,
        workflow: WorkflowTemplate | dict | Any,
        description: str | dict | Any = "",
    ) -> WorkflowVersion:
        # Handle dict payload
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId", "business_id")
            wf = _get(data, "workflow", "template", "workflow_template")
            desc = _get(data, "description", "desc")
            if tid is not None:
                tenant_id = tid
            if wf is not None and workflow is None:
                workflow = wf
            if desc is not None and not description:
                description = desc
        tenant_id = self._validate_tenant_id(tenant_id)
        workflow = self._validate_workflow(workflow)
        if isinstance(description, dict):
            description = str(_get(_unwrap(description), "description", "desc") or "")
        if not isinstance(description, str):
            description = str(description)
        description = description.strip()

        latest = self.repository.latest(
            tenant_id
        )

        version_number = (

            1

            if latest is None

            else latest.version + 1

        )

        version = WorkflowVersion(

            version_id=(
                f"{tenant_id}_v{version_number}"
            ),

            tenant_id=tenant_id,

            workflow_id=workflow.template_id,

            version=version_number,

            workflow=deepcopy(workflow),

            description=description,

        )

        return self.repository.save(
            version
        )

    def latest(
        self,
        tenant_id: str | dict | Any,
    ) -> WorkflowVersion | None:
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.repository.latest(
            tenant_id
        )

    def history(
        self,
        tenant_id: str | dict | Any,
    ) -> list[WorkflowVersion]:
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.repository.list(
            tenant_id
        )

    def get_version(
        self,
        tenant_id: str | dict | Any,
        version_number: int | str | dict | Any = None,
    ) -> WorkflowVersion | None:
        # Handle dict payload
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            vn = _get(data, "version", "version_number", "versionNumber")
            if tid is not None:
                tenant_id = tid
            if vn is not None and version_number is None:
                version_number = vn
        tenant_id = self._validate_tenant_id(tenant_id)
        if isinstance(version_number, dict):
            version_number = _get(_unwrap(version_number), "version", "version_number") or version_number
        if isinstance(version_number, str):
            version_number = int(version_number.strip())
        if not isinstance(version_number, int):
            raise ValueError("version_number must be an integer >= 1")
        return self.repository.get(tenant_id, version_number)

    def count(
        self,
        tenant_id: str | dict | Any,
    ) -> int:
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.repository.count(tenant_id)

    def health(self):

        return {

            "service": "workflow_version_manager",

            "status": "healthy",

        }
