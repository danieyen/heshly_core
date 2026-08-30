from __future__ import annotations

import threading

from heshly_core.models.workflow_assignment import (
    WorkflowAssignment,
)


class WorkflowAssignmentRepository:

    def __init__(self):

        self._assignments: dict[
            str,
            WorkflowAssignment,
        ] = {}
        self._lock = threading.RLock()

    def _validate_tenant_id(self, tenant_id: str):
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

    def save(
        self,
        assignment: WorkflowAssignment,
    ) -> WorkflowAssignment:
        if not isinstance(assignment, WorkflowAssignment):
            raise ValueError("assignment must be a WorkflowAssignment instance")
        self._validate_tenant_id(assignment.tenant_id)
        with self._lock:
            self._assignments[
                assignment.tenant_id
            ] = assignment
        return assignment

    def get(
        self,
        tenant_id: str,
    ) -> WorkflowAssignment | None:
        self._validate_tenant_id(tenant_id)
        with self._lock:
            return self._assignments.get(
                tenant_id.strip()
            )

    def delete(
        self,
        tenant_id: str,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        with self._lock:
            return self._assignments.pop(
                tenant_id.strip(),
                None,
            ) is not None

    def exists(
        self,
        tenant_id: str,
    ) -> bool:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            return False
        with self._lock:
            return tenant_id.strip() in self._assignments

    def list_all(self) -> list[WorkflowAssignment]:
        with self._lock:
            return list(self._assignments.values())

    def clear(self) -> None:
        with self._lock:
            self._assignments.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._assignments)
