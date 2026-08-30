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

    def _validate_tenant_id(self, tenant_id: str):
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

    def _validate_industry(self, industry: str) -> str:
        if not isinstance(industry, str) or not industry.strip():
            raise ValueError("industry must be a non-empty string")
        return industry.strip().lower()

    def assign(
        self,
        tenant_id: str,
        industry: str,
    ) -> WorkflowAssignment:
        self._validate_tenant_id(tenant_id)
        normalized_industry = self._validate_industry(industry)

        template = deepcopy(
            self.templates.load(
                normalized_industry
            )
        )

        assignment = WorkflowAssignment(

            assignment_id=(
                f"{tenant_id.strip()}_{normalized_industry}"
            ),

            tenant_id=tenant_id.strip(),

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
        self._validate_tenant_id(tenant_id)
        return self.repository.get(
            tenant_id.strip()
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            return False
        return self.repository.exists(tenant_id.strip())

    def remove(
        self,
        tenant_id: str,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        return self.repository.delete(
            tenant_id.strip()
        )

    def reassign(
        self,
        tenant_id: str,
        industry: str,
    ) -> WorkflowAssignment:
        # Reassign overwrites existing assignment
        return self.assign(tenant_id, industry)

    def health(self):

        return {

            "service": (
                "workflow_assignment_manager"
            ),

            "status": "healthy",

        }
