from __future__ import annotations

from copy import deepcopy

from heshly_core.models.workflow_template import (
    WorkflowTemplate,
)
from heshly_core.models.workflow_version import (
    WorkflowVersion,
)
from heshly_core.repositories.workflow_version_repository import (
    WorkflowVersionRepository,
)


class WorkflowVersionManager:
    """
    Workflow Version Manager.
    """

    def __init__(self):

        self.repository = (
            WorkflowVersionRepository()
        )

    def _validate_tenant_id(self, tenant_id: str):
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

    def _validate_workflow(self, workflow: WorkflowTemplate):
        if not isinstance(workflow, WorkflowTemplate):
            raise ValueError("workflow must be a WorkflowTemplate instance")
        if not workflow.template_id.strip():
            raise ValueError("workflow.template_id must be non-empty")

    def create_version(
        self,
        tenant_id: str,
        workflow: WorkflowTemplate,
        description: str = "",
    ) -> WorkflowVersion:
        self._validate_tenant_id(tenant_id)
        self._validate_workflow(workflow)
        if not isinstance(description, str):
            raise ValueError("description must be a string")

        tenant_id = tenant_id.strip()
        description = description.strip()

        latest = self.repository.latest(
            tenant_id
        )

        version_number = (

            1

            if latest is None

            else latest.version + 1

        )

        version = WorkflowVersion(

            version_id=(
                f"{tenant_id}_v{version_number}"
            ),

            tenant_id=tenant_id,

            workflow_id=workflow.template_id,

            version=version_number,

            workflow=deepcopy(workflow),

            description=description,

        )

        return self.repository.save(
            version
        )

    def latest(
        self,
        tenant_id: str,
    ) -> WorkflowVersion | None:
        self._validate_tenant_id(tenant_id)
        return self.repository.latest(
            tenant_id.strip()
        )

    def history(
        self,
        tenant_id: str,
    ) -> list[WorkflowVersion]:
        self._validate_tenant_id(tenant_id)
        return self.repository.list(
            tenant_id.strip()
        )

    def get_version(
        self,
        tenant_id: str,
        version_number: int,
    ) -> WorkflowVersion | None:
        self._validate_tenant_id(tenant_id)
        return self.repository.get(tenant_id.strip(), version_number)

    def count(
        self,
        tenant_id: str,
    ) -> int:
        self._validate_tenant_id(tenant_id)
        return self.repository.count(tenant_id.strip())

    def health(self):

        return {

            "service": "workflow_version_manager",

            "status": "healthy",

        }
