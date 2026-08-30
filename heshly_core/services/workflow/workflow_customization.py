from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.workflow_template import (
    WorkflowStep,
    WorkflowTemplate,
)


class WorkflowCustomization:
    """
    Workflow Customization Service.

    Provides tenant-specific customization
    of assigned workflow templates.
    """

    def _touch(self, workflow: WorkflowTemplate):
        workflow.updated_at = datetime.now(UTC)

    def _validate_workflow(self, workflow: WorkflowTemplate):
        if not isinstance(workflow, WorkflowTemplate):
            raise ValueError("workflow must be a WorkflowTemplate instance")

    def _validate_step_id(self, step_id: str):
        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError("step_id must be a non-empty string")

    def rename_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
        new_name: str,
    ) -> bool:
        self._validate_workflow(workflow)
        self._validate_step_id(step_id)
        if not isinstance(new_name, str) or not new_name.strip():
            raise ValueError("new_name must be a non-empty string")

        for step in workflow.steps:

            if step.step_id == step_id.strip():

                step.name = new_name.strip()
                self._touch(workflow)

                return True

        return False

    def enable_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
    ) -> bool:
        self._validate_workflow(workflow)
        self._validate_step_id(step_id)

        for step in workflow.steps:

            if step.step_id == step_id.strip():

                if not step.enabled:
                    step.enabled = True
                    self._touch(workflow)

                return True

        return False

    def disable_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
    ) -> bool:
        self._validate_workflow(workflow)
        self._validate_step_id(step_id)

        for step in workflow.steps:

            if step.step_id == step_id.strip():

                if step.enabled:
                    step.enabled = False
                    self._touch(workflow)

                return True

        return False

    def reorder_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
        new_order: int,
    ) -> bool:
        self._validate_workflow(workflow)
        self._validate_step_id(step_id)
        if not isinstance(new_order, int) or new_order < 1:
            raise ValueError("new_order must be an integer >= 1")

        target = None

        for step in workflow.steps:

            if step.step_id == step_id.strip():

                target = step

                break

        if target is None:

            return False

        target.order = new_order

        workflow.steps.sort(
            key=lambda s: s.order
        )
        self._touch(workflow)

        return True

    def add_step(
        self,
        workflow: WorkflowTemplate,
        step: WorkflowStep,
    ):
        self._validate_workflow(workflow)
        if not isinstance(step, WorkflowStep):
            raise ValueError("step must be a WorkflowStep instance")
        # Delegate to template which validates duplicates and touches
        workflow.add_step(step)

    def remove_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
    ) -> bool:
        self._validate_workflow(workflow)
        self._validate_step_id(step_id)

        original = len(workflow.steps)

        workflow.steps = [

            step

            for step in workflow.steps

            if step.step_id != step_id.strip()

        ]

        removed = len(workflow.steps) != original
        if removed:
            self._touch(workflow)
        return removed

    def health(self):

        return {

            "service": "workflow_customization",

            "status": "healthy",

        }
