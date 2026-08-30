from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from heshly_core.models.workflow_template import (
    WorkflowTemplate,
)


@dataclass(slots=True)
class WorkflowVersion:
    """
    Snapshot of a workflow at a point in time.
    Immutable snapshot - workflow is deepcopied on creation.
    """

    version_id: str

    tenant_id: str

    workflow_id: str

    version: int

    workflow: WorkflowTemplate

    description: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self):
        if not isinstance(self.version_id, str) or not self.version_id.strip():
            raise ValueError("version_id must be a non-empty string")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")
        if not isinstance(self.workflow_id, str) or not self.workflow_id.strip():
            raise ValueError("workflow_id must be a non-empty string")
        if not isinstance(self.version, int) or self.version < 1:
            raise ValueError("version must be an integer >= 1")
        if not isinstance(self.workflow, WorkflowTemplate):
            raise ValueError("workflow must be a WorkflowTemplate instance")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime")
        self.version_id = self.version_id.strip()
        self.tenant_id = self.tenant_id.strip()
        self.workflow_id = self.workflow_id.strip()
        self.description = self.description.strip()
        # Ensure snapshot isolation - deepcopy if not already
        object.__setattr__(self, "workflow", deepcopy(self.workflow))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "version": self.version,
            "workflow": self.workflow.to_dict(),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "WorkflowVersion":
        if not isinstance(data, dict):
            raise ValueError("WorkflowVersion data must be a dict")
        workflow_data = data.get("workflow")
        if not isinstance(workflow_data, dict):
            raise ValueError("workflow must be a dict")
        return cls(
            version_id=str(data.get("version_id", "")).strip(),
            tenant_id=str(data.get("tenant_id", "")).strip(),
            workflow_id=str(data.get("workflow_id", "")).strip(),
            version=int(data.get("version", 1)),
            workflow=WorkflowTemplate.from_dict(workflow_data),
            description=str(data.get("description", "")).strip(),
        )
