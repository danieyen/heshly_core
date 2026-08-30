from __future__ import annotations

import json
from typing import Any

from heshly_core.models.workflow_template import (
    WorkflowStep,
    WorkflowTemplate,
)

from heshly_core.services.workflow.workflow_assignment_manager import (
    WorkflowAssignmentManager,
)
from heshly_core.services.workflow.workflow_customization import (
    WorkflowCustomization,
)
from heshly_core.services.workflow.workflow_version_manager import (
    WorkflowVersionManager,
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
    if data is None:
        return {}
    if isinstance(data, str):
        parsed = _parse_json_string(data)
        if isinstance(parsed, dict):
            return parsed
        return {}
    if isinstance(data, dict):
        # handle n8n wrapping
        for key in ("$json", "json", "body", "data", "payload"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    # merge
                    merged = dict(data)
                    merged.pop(key, None)
                    for k, v in val.items():
                        if k not in merged or merged[k] in (None, ""):
                            merged[k] = v
                    return _unwrap(merged)
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

class WorkflowManager:
    """
    Tenant Workflow Manager.

    Central orchestration service for
    tenant workflow management.
    Tolerant to n8n JSON strings and $json/body nesting.
    """

    def __init__(self):

        self.assignment_manager = (
            WorkflowAssignmentManager()
        )

        self.customization = (
            WorkflowCustomization()
        )

        self.version_manager = (
            WorkflowVersionManager()
        )

    def _validate_tenant_id(self, tenant_id: Any) -> str:
        # tolerant: handle dict payload, JSON string, nested
        if isinstance(tenant_id, dict):
            unwrapped = _unwrap(tenant_id)
            tid = _get(unwrapped, "tenant_id", "tenantId", "business_id", "businessId")
            if tid is not None:
                tenant_id = tid
            else:
                # try to extract from any key
                for v in unwrapped.values():
                    if isinstance(v, str) and v.strip():
                        tenant_id = v
                        break
        if isinstance(tenant_id, str):
            parsed = _parse_json_string(tenant_id)
            if isinstance(parsed, dict):
                tid = _get(parsed, "tenant_id", "tenantId")
                if tid is not None:
                    tenant_id = tid
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return tenant_id.strip()

    def _validate_industry(self, industry: Any) -> str:
        if isinstance(industry, dict):
            unwrapped = _unwrap(industry)
            ind = _get(unwrapped, "industry", "industry_type", "template_id", "templateId")
            if ind is not None:
                industry = ind
        if isinstance(industry, str):
            parsed = _parse_json_string(industry)
            if isinstance(parsed, dict):
                ind = _get(parsed, "industry", "template_id")
                if ind is not None:
                    industry = ind
        if not isinstance(industry, str) or not industry.strip():
            raise ValueError("industry must be a non-empty string")
        return industry.strip()

    # =====================================================
    # Assignment
    # =====================================================

    def assign_workflow(
        self,
        tenant_id: str | dict | Any,
        industry: str | dict | Any = None,
    ) -> WorkflowTemplate:
        # Handle single dict payload: assign_workflow({"tenant_id": "...", "industry": "..."})
        if industry is None and isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId", "business_id")
            ind = _get(data, "industry", "industry_type", "template_id", "templateId")
            if tid is not None:
                tenant_id = tid
            if ind is not None:
                industry = ind
        if isinstance(tenant_id, str):
            parsed = _parse_json_string(tenant_id)
            if isinstance(parsed, dict):
                data = _unwrap(parsed)
                tid = _get(data, "tenant_id", "tenantId")
                ind = _get(data, "industry", "industry_type")
                if tid is not None:
                    tenant_id = tid
                if ind is not None and industry is None:
                    industry = ind
        tenant_id = self._validate_tenant_id(tenant_id)
        if industry is None:
            raise ValueError("industry must be a non-empty string")
        industry = self._validate_industry(industry)

        assignment = (
            self.assignment_manager.assign(
                tenant_id=tenant_id,
                industry=industry,
            )
        )

        self.version_manager.create_version(

            tenant_id=tenant_id,

            workflow=assignment.template,

            description="Initial workflow",

        )

        return assignment.template

    def workflow(
        self,
        tenant_id: str | dict | Any,
    ) -> WorkflowTemplate | None:
        tenant_id = self._validate_tenant_id(tenant_id)

        assignment = (
            self.assignment_manager.get(
                tenant_id
            )
        )

        if assignment is None:

            return None

        return assignment.template

    def get_assignment(self, tenant_id: str | dict | Any):
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.assignment_manager.get(tenant_id)

    def remove_workflow(self, tenant_id: str | dict | Any) -> bool:
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.assignment_manager.remove(tenant_id)

    def execute_workflow(
        self,
        tenant_id: str | dict | Any,
        step_id: str | None = None,
        payload: Any = None,
    ) -> dict[str, Any]:
        """
        Execute workflow for n8n Execute Workflow node.
        Tolerant to dict payloads and JSON strings.
        Returns dict with success boolean - never raises for n8n.
        """
        # Handle payload as first arg
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId", "business_id")
            sid = _get(data, "step_id", "stepId", "step", "id")
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = str(sid)
            if payload is None and data:
                payload = data
        tenant_id = self._validate_tenant_id(tenant_id)
        wf = self.workflow(tenant_id)
        if wf is None:
            # try to auto-assign if payload contains industry
            if isinstance(payload, dict):
                ind = _get(_unwrap(payload), "industry", "industry_type", "template_id")
                if ind:
                    wf = self.assign_workflow(tenant_id, str(ind))
            if wf is None:
                return {"success": False, "error": "workflow not found", "tenant_id": tenant_id}
        if step_id is not None:
            step_id = str(step_id).strip()
            if step_id and not wf.has_step(step_id):
                return {"success": False, "error": f"step_id '{step_id}' not found", "workflow": wf.to_dict()}
        return {"success": True, "tenant_id": tenant_id, "workflow": wf.to_dict(), "executed": True}

    # =====================================================
    # Customization
    # =====================================================

    def rename_step(
        self,
        tenant_id: str | dict | Any,
        step_id: str | dict | Any = None,
        new_name: str | dict | Any = None,
    ) -> bool:
        # Handle dict payload
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            sid = _get(data, "step_id", "stepId")
            nn = _get(data, "new_name", "newName", "name")
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
            if nn is not None and new_name is None:
                new_name = nn
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None or new_name is None:
            raise ValueError("step_id and new_name are required")
        if isinstance(step_id, dict):
            step_id = str(_get(_unwrap(step_id), "step_id", "stepId") or step_id)
        if isinstance(new_name, dict):
            new_name = str(_get(_unwrap(new_name), "new_name", "newName", "name") or new_name)
        step_id = str(step_id).strip()
        new_name = str(new_name).strip()

        workflow = self.workflow(
            tenant_id
        )

        if workflow is None:

            return False

        changed = self.customization.rename_step(

            workflow,

            step_id,

            new_name,

        )

        if changed:

            self.version_manager.create_version(

                tenant_id=tenant_id,

                workflow=workflow,

                description=f"Renamed step {step_id}",

            )

        return changed

    def enable_step(
        self,
        tenant_id: str | dict | Any,
        step_id: str | dict | Any = None,
    ) -> bool:
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            sid = _get(data, "step_id", "stepId")
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None:
            raise ValueError("step_id is required")
        step_id = str(step_id).strip()
        workflow = self.workflow(tenant_id)
        if workflow is None:
            return False
        changed = self.customization.enable_step(workflow, step_id)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id,
                workflow=workflow,
                description=f"Enabled step {step_id}",
            )
        return changed

    def disable_step(
        self,
        tenant_id: str | dict | Any,
        step_id: str | dict | Any = None,
    ) -> bool:
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            sid = _get(data, "step_id", "stepId")
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None:
            raise ValueError("step_id is required")
        step_id = str(step_id).strip()
        workflow = self.workflow(tenant_id)
        if workflow is None:
            return False
        changed = self.customization.disable_step(workflow, step_id)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id,
                workflow=workflow,
                description=f"Disabled step {step_id}",
            )
        return changed

    def reorder_step(
        self,
        tenant_id: str | dict | Any,
        step_id: str | dict | Any = None,
        new_order: int | dict | Any = None,
    ) -> bool:
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            sid = _get(data, "step_id", "stepId")
            no = _get(data, "new_order", "newOrder", "order")
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
            if no is not None and new_order is None:
                new_order = no
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None or new_order is None:
            raise ValueError("step_id and new_order are required")
        step_id = str(step_id).strip()
        if isinstance(new_order, dict):
            new_order = _get(_unwrap(new_order), "new_order", "newOrder", "order") or new_order
        new_order = int(str(new_order).strip()) if isinstance(new_order, str) else int(new_order)
        workflow = self.workflow(tenant_id)
        if workflow is None:
            return False
        changed = self.customization.reorder_step(workflow, step_id, new_order)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id,
                workflow=workflow,
                description=f"Reordered step {step_id} to {new_order}",
            )
        return changed

    def remove_step(
        self,
        tenant_id: str | dict | Any,
        step_id: str | dict | Any = None,
    ) -> bool:
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            sid = _get(data, "step_id", "stepId")
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None:
            raise ValueError("step_id is required")
        step_id = str(step_id).strip()
        workflow = self.workflow(tenant_id)
        if workflow is None:
            return False
        changed = self.customization.remove_step(workflow, step_id)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id,
                workflow=workflow,
                description=f"Removed step {step_id}",
            )
        return changed

    def add_step(
        self,
        tenant_id: str | dict | Any,
        step: WorkflowStep | dict | Any = None,
    ) -> bool:
        if isinstance(tenant_id, dict) and step is None:
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId")
            s = _get(data, "step", "workflow_step", "workflowStep")
            if tid is not None:
                tenant_id = tid
            if s is not None:
                step = s
            # also handle flat step fields in same dict
            if step is None and _get(data, "step_id", "stepId") is not None:
                step = data
        tenant_id = self._validate_tenant_id(tenant_id)
        if step is None:
            raise ValueError("step must be a WorkflowStep instance")
        if isinstance(step, dict):
            # tolerant: handle capitalized keys, JSON strings
            step = _unwrap(step)
            # map capitalized keys
            mapped = {}
            for k, v in step.items():
                lk = str(k).lower().replace("_","").replace("-","")
                if lk in ("stepid", "id"):
                    mapped["step_id"] = v
                elif lk == "name":
                    mapped["name"] = v
                elif lk == "action":
                    mapped["action"] = v
                elif lk == "order":
                    mapped["order"] = v
                elif lk == "enabled":
                    mapped["enabled"] = v
                else:
                    mapped[k] = v
            step = WorkflowStep.from_dict(mapped)
        if not isinstance(step, WorkflowStep):
            raise ValueError("step must be a WorkflowStep instance")

        workflow = self.workflow(
            tenant_id
        )

        if workflow is None:

            return False

        self.customization.add_step(
            workflow,
            step,
        )

        self.version_manager.create_version(

            tenant_id=tenant_id,

            workflow=workflow,

            description="Added workflow step",

        )

        return True

    # =====================================================
    # Versioning
    # =====================================================

    def history(
        self,
        tenant_id: str | dict | Any,
    ):
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.version_manager.history(
            tenant_id
        )

    def latest_version(self, tenant_id: str | dict | Any):
        tenant_id = self._validate_tenant_id(tenant_id)
        return self.version_manager.latest(tenant_id)

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "workflow_manager",

            "status": "healthy",

        }
