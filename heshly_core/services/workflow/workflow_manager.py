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
        # handle n8n wrapping and __rl
        for key in ("$json", "json", "body", "data", "payload"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    merged = dict(data)
                    merged.pop(key, None)
                    for k, v in val.items():
                        if isinstance(v, dict) and "__rl" in v and "value" in v:
                            v = str(v["value"]).strip()
                        if k not in merged or merged[k] in (None, ""):
                            merged[k] = v
                    return _unwrap(merged)
        # unwrap __rl values
        for k, v in list(data.items()):
            if isinstance(v, dict) and "__rl" in v and "value" in v:
                data[k] = str(v["value"]).strip()
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
    Tolerant to n8n JSON strings and $json/body nesting and __rl workflowId.
    Handles WF3 Parent -> WF3/2 -> WF4 WhatsApp Response chain via registry fallback.
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
        if isinstance(tenant_id, dict):
            # handle __rl
            if "__rl" in tenant_id and "value" in tenant_id:
                tenant_id = tenant_id["value"]
            else:
                unwrapped = _unwrap(tenant_id)
                tid = _get(unwrapped, "tenant_id", "tenantId", "business_id", "businessId")
                if tid is not None:
                    tenant_id = tid
                else:
                    for v in unwrapped.values():
                        if isinstance(v, str) and v.strip():
                            tenant_id = v
                            break
        if isinstance(tenant_id, str):
            parsed = _parse_json_string(tenant_id)
            if isinstance(parsed, dict):
                if "__rl" in parsed and "value" in parsed:
                    tenant_id = parsed["value"]
                else:
                    tid = _get(parsed, "tenant_id", "tenantId")
                    if tid is not None:
                        tenant_id = tid
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        return tenant_id.strip()

    def _validate_industry(self, industry: Any) -> str:
        if isinstance(industry, dict):
            if "__rl" in industry and "value" in industry:
                industry = industry["value"]
            else:
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

    def _extract_workflow_id(self, data: Any) -> str | None:
        if isinstance(data, dict):
            v = _get(_unwrap(data), "workflowId", "workflow_id", "workflowID", "id")
            if isinstance(v, dict) and "value" in v:
                v = v["value"]
            if isinstance(v, str) and v.strip():
                return v.strip()
        if isinstance(data, str) and data.strip():
            # check if it's a UUID
            v = data.strip()
            if len(v) == 36 and v.count("-") == 4:
                return v
        return None

    # =====================================================
    # Assignment
    # =====================================================

    def assign_workflow(
        self,
        tenant_id: str | dict | Any,
        industry: str | dict | Any = None,
    ) -> WorkflowTemplate:
        if industry is None and isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId", "business_id")
            ind = _get(data, "industry", "industry_type", "template_id", "templateId")
            # also handle workflowId -> industry via registry (WF3 Parent / WF4)
            wid = _get(data, "workflowId", "workflow_id")
            if isinstance(wid, dict) and "value" in wid:
                wid = wid["value"]
            if wid and not ind:
                try:
                    from heshly_core.services.workflow.workflow_registry import get_registry
                    ind = get_registry().resolve_industry(str(wid))
                    if not ind and len(str(wid)) == 36:
                        ind = "dental"
                except Exception:
                    pass
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
        Tolerant to dict payloads, JSON strings, __rl workflowId.
        Returns dict with success boolean - never raises for n8n.
        Handles WF3 Parent -> WF3/2 -> WF4 chain via registry fallback.
        """
        # Handle payload as first arg with workflowId
        workflow_id = None
        if isinstance(tenant_id, dict):
            data = _unwrap(tenant_id)
            tid = _get(data, "tenant_id", "tenantId", "business_id")
            sid = _get(data, "step_id", "stepId", "step", "id")
            wid = _get(data, "workflowId", "workflow_id", "workflowID")
            if isinstance(wid, dict) and "value" in wid:
                wid = wid["value"]
            if wid is not None:
                workflow_id = str(wid).strip()
            if tid is not None:
                tenant_id = tid
            elif workflow_id:
                pass
            if sid is not None and step_id is None:
                step_id = str(sid)
            if payload is None and data:
                payload = data
        # also check payload for workflowId
        if isinstance(payload, dict):
            wid = _get(_unwrap(payload), "workflowId", "workflow_id")
            if isinstance(wid, dict) and "value" in wid:
                wid = wid["value"]
            if wid and not workflow_id:
                workflow_id = str(wid).strip()
        # If tenant_id is actually a workflowId UUID and no tenant provided, try registry
        if isinstance(tenant_id, str) and len(tenant_id.strip()) == 36 and tenant_id.strip().count("-") == 4:
            # looks like UUID, treat as workflowId
            if not workflow_id:
                workflow_id = tenant_id.strip()
            # try to get tenant from payload
            if isinstance(payload, dict):
                tid = _get(_unwrap(payload), "tenant_id", "tenantId")
                if tid:
                    tenant_id = tid
                else:
                    # no tenant - return template for workflowId (fallback for WF3 Parent / WF4)
                    try:
                        from heshly_core.services.workflow.workflow_registry import get_registry
                        industry = get_registry().resolve_industry(workflow_id)
                        if not industry:
                            industry = "dental"
                        template = self.assignment_manager.templates.load(industry)
                        return {"success": True, "workflowId": workflow_id, "industry": industry, "workflow": template.to_dict(), "executed": True, "message": "Executed via workflowId fallback"}
                    except Exception:
                        pass
                    raise ValueError("tenant_id must be a non-empty string")
        tenant_id = self._validate_tenant_id(tenant_id)
        wf = self.workflow(tenant_id)
        if wf is None:
            # try to auto-assign if payload contains industry or workflowId (WF3 Parent -> WF4)
            industry = None
            if isinstance(payload, dict):
                industry = _get(_unwrap(payload), "industry", "industry_type", "template_id")
                if isinstance(industry, dict) and "value" in industry:
                    industry = industry["value"]
            if not industry and workflow_id:
                try:
                    from heshly_core.services.workflow.workflow_registry import get_registry
                    industry = get_registry().resolve_industry(workflow_id)
                    if not industry and len(workflow_id) == 36:
                        industry = "dental"
                except Exception:
                    pass
            if industry:
                wf = self.assign_workflow(tenant_id, str(industry))
            if wf is None:
                return {"success": False, "error": "workflow not found", "tenant_id": tenant_id, "workflowId": workflow_id}
        if step_id is not None:
            step_id = str(step_id).strip()
            if step_id and not wf.has_step(step_id):
                return {"success": False, "error": f"step_id '{step_id}' not found", "workflow": wf.to_dict(), "workflowId": workflow_id}
        return {"success": True, "tenant_id": tenant_id, "workflowId": workflow_id, "workflow": wf.to_dict(), "executed": True}

    def execute_by_workflow_id(
        self,
        workflow_id: str | dict | Any,
        tenant_id: str | dict | Any = None,
        payload: Any = None,
    ) -> dict[str, Any]:
        """
        Execute by n8n workflowId (UUID). Resolves to industry via registry.
        Fixes 'Workflow does not exist' by mapping WF3 Parent, WF3/2, WF4 -> dental
        """
        if isinstance(workflow_id, dict) and "value" in workflow_id:
            workflow_id = workflow_id["value"]
        workflow_id = str(workflow_id).strip() if workflow_id is not None else ""
        if not workflow_id:
            raise ValueError("workflowId must be non-empty")
        # Resolve industry
        try:
            from heshly_core.services.workflow.workflow_registry import get_registry
            industry = get_registry().resolve_industry(workflow_id)
            if not industry and len(workflow_id) == 36:
                industry = "dental"
        except Exception:
            industry = None
        if not industry:
            return {"success": False, "error": f"workflowId '{workflow_id}' not found in registry", "workflowId": workflow_id, "hint": "Import n8n_workflows/WF3_Parent.json, WF3_2.json, WF4_WhatsApp_Response.json or call with tenant_id+industry"}
        # Need tenant_id
        if tenant_id is None and isinstance(payload, dict):
            tenant_id = _get(_unwrap(payload), "tenant_id", "tenantId", "business_id")
        if tenant_id is None:
            # Return template without tenant execution
            try:
                template = self.assignment_manager.templates.load(industry)
                return {"success": True, "workflowId": workflow_id, "industry": industry, "workflow": template.to_dict(), "executed": True, "message": "Resolved via registry (no tenant)"}
            except Exception as e:
                return {"success": False, "error": str(e), "workflowId": workflow_id}
        return self.execute_workflow(tenant_id, payload=payload)

    # =====================================================
    # Customization
    # =====================================================

    def rename_step(
        self,
        tenant_id: str | dict | Any,
        step_id: str | dict | Any = None,
        new_name: str | dict | Any = None,
    ) -> bool:
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
            if "__rl" in step_id and "value" in step_id:
                step_id = step_id["value"]
            else:
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
            if "__rl" in sid and isinstance(sid, dict) and "value" in sid:
                sid = sid["value"]
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None:
            raise ValueError("step_id is required")
        if isinstance(step_id, dict) and "__rl" in step_id and "value" in step_id:
            step_id = step_id["value"]
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
            if isinstance(sid, dict) and "__rl" in sid and "value" in sid:
                sid = sid["value"]
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None:
            raise ValueError("step_id is required")
        if isinstance(step_id, dict) and "__rl" in step_id and "value" in step_id:
            step_id = step_id["value"]
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
            if isinstance(sid, dict) and "__rl" in sid and "value" in sid:
                sid = sid["value"]
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
            if no is not None and new_order is None:
                new_order = no
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None or new_order is None:
            raise ValueError("step_id and new_order are required")
        if isinstance(step_id, dict) and "__rl" in step_id and "value" in step_id:
            step_id = step_id["value"]
        step_id = str(step_id).strip()
        if isinstance(new_order, dict):
            if "__rl" in new_order and "value" in new_order:
                new_order = new_order["value"]
            else:
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
            if isinstance(sid, dict) and "__rl" in sid and "value" in sid:
                sid = sid["value"]
            if tid is not None:
                tenant_id = tid
            if sid is not None and step_id is None:
                step_id = sid
        tenant_id = self._validate_tenant_id(tenant_id)
        if step_id is None:
            raise ValueError("step_id is required")
        if isinstance(step_id, dict) and "__rl" in step_id and "value" in step_id:
            step_id = step_id["value"]
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
            if step is None and _get(data, "step_id", "stepId") is not None:
                step = data
        tenant_id = self._validate_tenant_id(tenant_id)
        if step is None:
            raise ValueError("step must be a WorkflowStep instance")
        if isinstance(step, dict):
            step = _unwrap(step)
            mapped = {}
            for k, v in step.items():
                if isinstance(v, dict) and "__rl" in v and "value" in v:
                    v = v["value"]
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
