from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from heshly_core.models.workflow_template import (
    WorkflowTemplate,
)


@dataclass(slots=True)
class WorkflowVersion:
    """
    Snapshot of a workflow at a point in time.
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