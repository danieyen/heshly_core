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

    def _validate_tenant_id(self, tenant_id: str):
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

    # =====================================================
    # Assignment
    # =====================================================

    def assign_workflow(
        self,
        tenant_id: str,
        industry: str,
    ) -> WorkflowTemplate:
        self._validate_tenant_id(tenant_id)
        if not isinstance(industry, str) or not industry.strip():
            raise ValueError("industry must be a non-empty string")

        assignment = (
            self.assignment_manager.assign(
                tenant_id=tenant_id.strip(),
                industry=industry.strip(),
            )
        )

        self.version_manager.create_version(

            tenant_id=tenant_id.strip(),

            workflow=assignment.template,

            description="Initial workflow",

        )

        return assignment.template

    def workflow(
        self,
        tenant_id: str,
    ) -> WorkflowTemplate | None:
        self._validate_tenant_id(tenant_id)

        assignment = (
            self.assignment_manager.get(
                tenant_id.strip()
            )
        )

        if assignment is None:

            return None

        return assignment.template

    def get_assignment(self, tenant_id: str):
        self._validate_tenant_id(tenant_id)
        return self.assignment_manager.get(tenant_id.strip())

    def remove_workflow(self, tenant_id: str) -> bool:
        self._validate_tenant_id(tenant_id)
        return self.assignment_manager.remove(tenant_id.strip())

    # =====================================================
    # Customization
    # =====================================================

    def rename_step(
        self,
        tenant_id: str,
        step_id: str,
        new_name: str,
    ) -> bool:
        self._validate_tenant_id(tenant_id)

        workflow = self.workflow(
            tenant_id.strip()
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

                tenant_id=tenant_id.strip(),

                workflow=workflow,

                description=f"Renamed step {step_id}",

            )

        return changed

    def enable_step(
        self,
        tenant_id: str,
        step_id: str,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        workflow = self.workflow(tenant_id.strip())
        if workflow is None:
            return False
        changed = self.customization.enable_step(workflow, step_id)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id.strip(),
                workflow=workflow,
                description=f"Enabled step {step_id}",
            )
        return changed

    def disable_step(
        self,
        tenant_id: str,
        step_id: str,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        workflow = self.workflow(tenant_id.strip())
        if workflow is None:
            return False
        changed = self.customization.disable_step(workflow, step_id)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id.strip(),
                workflow=workflow,
                description=f"Disabled step {step_id}",
            )
        return changed

    def reorder_step(
        self,
        tenant_id: str,
        step_id: str,
        new_order: int,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        workflow = self.workflow(tenant_id.strip())
        if workflow is None:
            return False
        changed = self.customization.reorder_step(workflow, step_id, new_order)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id.strip(),
                workflow=workflow,
                description=f"Reordered step {step_id} to {new_order}",
            )
        return changed

    def remove_step(
        self,
        tenant_id: str,
        step_id: str,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        workflow = self.workflow(tenant_id.strip())
        if workflow is None:
            return False
        changed = self.customization.remove_step(workflow, step_id)
        if changed:
            self.version_manager.create_version(
                tenant_id=tenant_id.strip(),
                workflow=workflow,
                description=f"Removed step {step_id}",
            )
        return changed

    def add_step(
        self,
        tenant_id: str,
        step: WorkflowStep,
    ) -> bool:
        self._validate_tenant_id(tenant_id)
        if not isinstance(step, WorkflowStep):
            raise ValueError("step must be a WorkflowStep instance")

        workflow = self.workflow(
            tenant_id.strip()
        )

        if workflow is None:

            return False

        self.customization.add_step(
            workflow,
            step,
        )

        self.version_manager.create_version(

            tenant_id=tenant_id.strip(),

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
        self._validate_tenant_id(tenant_id)
        return self.version_manager.history(
            tenant_id.strip()
        )

    def latest_version(self, tenant_id: str):
        self._validate_tenant_id(tenant_id)
        return self.version_manager.latest(tenant_id.strip())

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "workflow_manager",

            "status": "healthy",

        }
