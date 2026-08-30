from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


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
            raise ValueError("order must be an integer >= 1")
        if not isinstance(self.enabled, bool):
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
        if not isinstance(data, dict):
            raise ValueError("WorkflowStep data must be a dict")
        return cls(
            step_id=str(data.get("step_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            action=str(data.get("action", "")).strip(),
            order=int(data.get("order", 1)),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(slots=True)
class WorkflowTemplate:
    """
    Tenant Workflow Template.
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
        return any(s.step_id == step_id for s in self.steps)

    def get_step(self, step_id: str) -> WorkflowStep | None:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def add_step(
        self,
        step: WorkflowStep,
    ):
        if not isinstance(step, WorkflowStep):
            raise ValueError("step must be a WorkflowStep instance")
        if self.has_step(step.step_id):
            raise ValueError(f"step_id '{step.step_id}' already exists")
        self.steps.append(step)
        self.steps.sort(key=lambda s: s.order)
        self._touch()

    def remove_step(self, step_id: str) -> bool:
        original = len(self.steps)
        self.steps = [s for s in self.steps if s.step_id != step_id]
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
        if not isinstance(data, dict):
            raise ValueError("WorkflowTemplate data must be a dict")
        steps_data = data.get("steps", [])
        steps = [WorkflowStep.from_dict(s) for s in steps_data] if isinstance(steps_data, list) else []
        return cls(
            template_id=str(data.get("template_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            industry=str(data.get("industry", "")).strip(),
            description=str(data.get("description", "")).strip(),
            steps=steps,
        )
