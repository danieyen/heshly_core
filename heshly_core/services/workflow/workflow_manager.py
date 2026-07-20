from __future__ import annotations

from heshly_core.models.workflow_template import (
    WorkflowStep,
    WorkflowTemplate,
)

from heshly_core.services.workflow.workflow_assignment_manager import (
    WorkflowAssignmentManager,
)
from heshly_core.services.workflow.workflow_customization import (
    WorkflowCustomization,
)
from heshly_core.services.workflow.workflow_version_manager import (
    WorkflowVersionManager,
)


class WorkflowManager:
    """
    Tenant Workflow Manager.

    Central orchestration service for
    tenant workflow management.
    """

    def __init__(self):

        self.assignment_manager = (
            WorkflowAssignmentManager()
        )

        self.customization = (
            WorkflowCustomization()
        )

        self.version_manager = (
            WorkflowVersionManager()
        )

    # =====================================================
    # Assignment
    # =====================================================

    def assign_workflow(
        self,
        tenant_id: str,
        industry: str,
    ) -> WorkflowTemplate:

        assignment = (
            self.assignment_manager.assign(
                tenant_id=tenant_id,
                industry=industry,
            )
        )

        self.version_manager.create_version(

            tenant_id=tenant_id,

            workflow=assignment.template,

            description="Initial workflow",

        )

        return assignment.template

    def workflow(
        self,
        tenant_id: str,
    ) -> WorkflowTemplate | None:

        assignment = (
            self.assignment_manager.get(
                tenant_id
            )
        )

        if assignment is None:

            return None

        return assignment.template

    # =====================================================
    # Customization
    # =====================================================

    def rename_step(
        self,
        tenant_id: str,
        step_id: str,
        new_name: str,
    ) -> bool:

        workflow = self.workflow(
            tenant_id
        )

        if workflow is None:

            return False

        changed = self.customization.rename_step(

            workflow,

            step_id,

            new_name,

        )

        if changed:

            self.version_manager.create_version(

                tenant_id=tenant_id,

                workflow=workflow,

                description=f"Renamed step {step_id}",

            )

        return changed

    def add_step(
        self,
        tenant_id: str,
        step: WorkflowStep,
    ) -> bool:

        workflow = self.workflow(
            tenant_id
        )

        if workflow is None:

            return False

        self.customization.add_step(
            workflow,
            step,
        )

        self.version_manager.create_version(

            tenant_id=tenant_id,

            workflow=workflow,

            description="Added workflow step",

        )

        return True

    # =====================================================
    # Versioning
    # =====================================================

    def history(
        self,
        tenant_id: str,
    ):

        return self.version_manager.history(
            tenant_id
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "workflow_manager",

            "status": "healthy",

        }