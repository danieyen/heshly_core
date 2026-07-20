from __future__ import annotations

from copy import deepcopy

from heshly_core.models.workflow_assignment import (
    WorkflowAssignment,
)
from heshly_core.repositories.workflow_assignment_repository import (
    WorkflowAssignmentRepository,
)
from heshly_core.services.workflow.workflow_templates import (
    WorkflowTemplates,
)


class WorkflowAssignmentManager:
    """
    Assigns workflow templates to tenants.
    """

    def __init__(self):

        self.templates = WorkflowTemplates()

        self.repository = (
            WorkflowAssignmentRepository()
        )

    def assign(
        self,
        tenant_id: str,
        industry: str,
    ) -> WorkflowAssignment:

        template = deepcopy(
            self.templates.load(
                industry
            )
        )

        assignment = WorkflowAssignment(

            assignment_id=(
                f"{tenant_id}_{industry}"
            ),

            tenant_id=tenant_id,

            template=template,

        )

        self.repository.save(
            assignment
        )

        return assignment

    def get(
        self,
        tenant_id: str,
    ) -> WorkflowAssignment | None:

        return self.repository.get(
            tenant_id
        )

    def remove(
        self,
        tenant_id: str,
    ) -> bool:

        return self.repository.delete(
            tenant_id
        )

    def health(self):

        return {

            "service": (
                "workflow_assignment_manager"
            ),

            "status": "healthy",

        }