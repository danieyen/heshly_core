from __future__ import annotations

from heshly_core.models.workflow_assignment import (
    WorkflowAssignment,
)


class WorkflowAssignmentRepository:

    def __init__(self):

        self._assignments: dict[
            str,
            WorkflowAssignment,
        ] = {}

    def save(
        self,
        assignment: WorkflowAssignment,
    ) -> WorkflowAssignment:

        self._assignments[
            assignment.tenant_id
        ] = assignment

        return assignment

    def get(
        self,
        tenant_id: str,
    ) -> WorkflowAssignment | None:

        return self._assignments.get(
            tenant_id
        )

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        return self._assignments.pop(
            tenant_id,
            None,
        ) is not None

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return tenant_id in self._assignments