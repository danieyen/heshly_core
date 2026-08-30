from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


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

def _get_case_insensitive(data: dict, *candidates: str) -> Any | None:
    if not isinstance(data, dict):
        return None
    lower = {str(k).lower().replace("_","").replace("-",""): v for k, v in data.items() if isinstance(k, str)}
    for c in candidates:
        if c in data and data[c] not in (None, ""):
            return data[c]
        lc = c.lower().replace("_","").replace("-","")
        if lc in lower and lower[lc] not in (None, ""):
            return lower[lc]
        # Capitalized
        cap = c.capitalize()
        if cap in data and data[cap] not in (None, ""):
            return data[cap]
    return None

@dataclass(slots=True)
class WorkflowStep:

    step_id: str

    name: str

    action: str

    order: int

    enabled: bool = True

    def __post_init__(self):
        if not isinstance(self.step_id, str) or not self.step_id.strip():
            raise ValueError("step_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.action, str) or not self.action.strip():
            raise ValueError("action must be a non-empty string")
        if not isinstance(self.order, int) or self.order < 1:
            try:
                # tolerant: coerce string numbers
                if isinstance(self.order, str):
                    object.__setattr__(self, "order", int(self.order.strip()))
                else:
                    object.__setattr__(self, "order", int(self.order))
            except Exception:
                raise ValueError("order must be an integer >= 1")
            if self.order < 1:
                raise ValueError("order must be an integer >= 1")
        if not isinstance(self.enabled, bool):
            # tolerant: coerce string booleans
            if isinstance(self.enabled, str):
                v = self.enabled.strip().lower()
                if v in ("true", "1", "yes", "enabled"):
                    object.__setattr__(self, "enabled", True)
                elif v in ("false", "0", "no", "disabled"):
                    object.__setattr__(self, "enabled", False)
                else:
                    raise ValueError("enabled must be a boolean")
            elif isinstance(self.enabled, int):
                object.__setattr__(self, "enabled", bool(self.enabled))
            else:
                raise ValueError("enabled must be a boolean")
        self.step_id = self.step_id.strip()
        self.name = self.name.strip()
        self.action = self.action.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "action": self.action,
            "order": self.order,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "WorkflowStep":
        if isinstance(data, str):
            data = _parse_json_string(data)
        if not isinstance(data, dict):
            raise ValueError("WorkflowStep data must be a dict")
        # handle n8n wrapping
        for key in ("$json", "json", "body", "data", "step", "workflow_step"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    data = val
                    break
        step_id = _get_case_insensitive(data, "step_id", "stepId", "id")
        name = _get_case_insensitive(data, "name", "step_name", "stepName")
        action = _get_case_insensitive(data, "action", "step_action", "stepAction")
        order = _get_case_insensitive(data, "order", "step_order", "stepOrder", "position")
        enabled = _get_case_insensitive(data, "enabled", "is_enabled", "isEnabled", "active")
        if enabled is None:
            enabled = True
        return cls(
            step_id=str(step_id).strip() if step_id is not None else "",
            name=str(name).strip() if name is not None else "",
            action=str(action).strip() if action is not None else "",
            order=int(str(order).strip()) if isinstance(order, str) and str(order).strip().isdigit() else int(order) if order is not None else 1,
            enabled=bool(enabled) if not isinstance(enabled, str) else enabled.lower() not in ("false", "0", "no", "disabled"),
        )


@dataclass(slots=True)
class WorkflowTemplate:
    """
    Tenant Workflow Template.
    Tolerant to n8n capitalized keys and JSON strings.
    """

    template_id: str

    name: str

    industry: str

    description: str = ""

    steps: list[WorkflowStep] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self):
        if not isinstance(self.template_id, str) or not self.template_id.strip():
            raise ValueError("template_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.industry, str) or not self.industry.strip():
            raise ValueError("industry must be a non-empty string")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
        if not isinstance(self.steps, list):
            raise ValueError("steps must be a list")
        for s in self.steps:
            if not isinstance(s, WorkflowStep):
                raise ValueError("steps must contain only WorkflowStep instances")
        self.template_id = self.template_id.strip()
        self.name = self.name.strip()
        self.industry = self.industry.strip()
        self.description = self.description.strip()
        self.steps.sort(key=lambda s: s.order)

    def _touch(self):
        self.updated_at = datetime.now(UTC)

    def has_step(self, step_id: str) -> bool:
        if not step_id:
            return False
        # tolerant: strip and case-sensitive but handle string coercion
        sid = str(step_id).strip()
        return any(s.step_id == sid for s in self.steps)

    def get_step(self, step_id: str) -> WorkflowStep | None:
        sid = str(step_id).strip() if step_id is not None else ""
        for s in self.steps:
            if s.step_id == sid:
                return s
        return None

    def add_step(
        self,
        step: WorkflowStep,
    ):
        if isinstance(step, dict):
            step = WorkflowStep.from_dict(step)
        if isinstance(step, str):
            step = WorkflowStep.from_dict(_parse_json_string(step))
        if not isinstance(step, WorkflowStep):
            raise ValueError("step must be a WorkflowStep instance")
        if self.has_step(step.step_id):
            raise ValueError(f"step_id '{step.step_id}' already exists")
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)
        self._touch()

    def remove_step(self, step_id: str) -> bool:
        sid = str(step_id).strip() if step_id is not None else ""
        original = len(self.steps)
        self.steps = [s for s in self.steps if s.step_id != sid]
        removed = len(self.steps) != original
        if removed:
            self._touch()
        return removed

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.template_id.strip():
            errors.append("template_id is required")
        if not self.name.strip():
            errors.append("name is required")
        if not self.industry.strip():
            errors.append("industry is required")
        seen_ids: set[str] = set()
        seen_orders: set[int] = set()
        for s in self.steps:
            if s.step_id in seen_ids:
                errors.append(f"duplicate step_id: {s.step_id}")
            seen_ids.add(s.step_id)
            if s.order in seen_orders:
                errors.append(f"duplicate order: {s.order}")
            seen_orders.add(s.order)
        return errors

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def enabled_steps(self) -> list[WorkflowStep]:
        return [s for s in self.steps if s.enabled]

    @property
    def enabled_step_count(self) -> int:
        return len(self.enabled_steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "industry": self.industry,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "WorkflowTemplate":
        if isinstance(data, str):
            data = _parse_json_string(data)
        if not isinstance(data, dict):
            raise ValueError("WorkflowTemplate data must be a dict")
        # handle n8n wrapping
        for key in ("$json", "json", "body", "data", "template", "workflow", "workflow_template"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict) and ("template_id" in val or "templateId" in val or "steps" in val):
                    data = val
                    break
        template_id = _get_case_insensitive(data, "template_id", "templateId", "id", "workflow_id", "workflowId")
        name = _get_case_insensitive(data, "name", "template_name", "templateName", "workflow_name")
        industry = _get_case_insensitive(data, "industry", "industry_type", "industryType")
        description = _get_case_insensitive(data, "description", "desc", "details")
        steps_data = _get_case_insensitive(data, "steps", "workflow_steps", "workflowSteps")
        if steps_data is None:
            steps_data = data.get("steps", [])
        steps = []
        if isinstance(steps_data, str):
            steps_data = _parse_json_string(steps_data)
        if isinstance(steps_data, list):
            for s in steps_data:
                try:
                    steps.append(WorkflowStep.from_dict(s))
                except Exception:
                    continue
        return cls(
            template_id=str(template_id).strip() if template_id is not None else "",
            name=str(name).strip() if name is not None else "",
            industry=str(industry).strip() if industry is not None else "",
            description=str(description).strip() if description is not None else "",
            steps=steps,
        )
