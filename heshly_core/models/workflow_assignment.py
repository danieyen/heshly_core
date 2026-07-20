from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

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

    def activate(self):

        self.active = True

    def deactivate(self):

        self.active = False