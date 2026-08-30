from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from heshly_core.models.workflow_template import (
    WorkflowTemplate,
)


@dataclass(slots=True)
class WorkflowAssignment:
    """
    Tenant Workflow Assignment.
    """

    assignment_id: str

    tenant_id: str

    template: WorkflowTemplate

    active: bool = True

    assigned_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self):
        if not isinstance(self.assignment_id, str) or not self.assignment_id.strip():
            raise ValueError("assignment_id must be a non-empty string")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        if not isinstance(self.template, WorkflowTemplate):
            raise ValueError("template must be a WorkflowTemplate instance")
        if not isinstance(self.active, bool):
            raise ValueError("active must be a boolean")
        if not isinstance(self.assigned_at, datetime):
            raise ValueError("assigned_at must be a datetime")
        self.assignment_id = self.assignment_id.strip()
        self.tenant_id = self.tenant_id.strip()

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    @property
    def is_active(self) -> bool:
        return bool(self.active)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "tenant_id": self.tenant_id,
            "template": self.template.to_dict(),
            "active": self.active,
            "assigned_at": self.assigned_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "WorkflowAssignment":
        if not isinstance(data, dict):
            raise ValueError("WorkflowAssignment data must be a dict")
        template_data = data.get("template")
        if not isinstance(template_data, dict):
            raise ValueError("template must be a dict")
        return cls(
            assignment_id=str(data.get("assignment_id", "")).strip(),
            tenant_id=str(data.get("tenant_id", "")).strip(),
            template=WorkflowTemplate.from_dict(template_data),
            active=bool(data.get("active", True)),
        )
