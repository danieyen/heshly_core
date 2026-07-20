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

    def create_version(
        self,
        tenant_id: str,
        workflow: WorkflowTemplate,
        description: str = "",
    ) -> WorkflowVersion:

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

        return self.repository.latest(
            tenant_id
        )

    def history(
        self,
        tenant_id: str,
    ) -> list[WorkflowVersion]:

        return self.repository.list(
            tenant_id
        )

    def health(self):

        return {

            "service": "workflow_version_manager",

            "status": "healthy",

        }