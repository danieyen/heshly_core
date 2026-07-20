from __future__ import annotations

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

    def rename_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
        new_name: str,
    ) -> bool:

        for step in workflow.steps:

            if step.step_id == step_id:

                step.name = new_name

                return True

        return False

    def enable_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
    ) -> bool:

        for step in workflow.steps:

            if step.step_id == step_id:

                step.enabled = True

                return True

        return False

    def disable_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
    ) -> bool:

        for step in workflow.steps:

            if step.step_id == step_id:

                step.enabled = False

                return True

        return False

    def reorder_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
        new_order: int,
    ) -> bool:

        target = None

        for step in workflow.steps:

            if step.step_id == step_id:

                target = step

                break

        if target is None:

            return False

        target.order = new_order

        workflow.steps.sort(
            key=lambda s: s.order
        )

        return True

    def add_step(
        self,
        workflow: WorkflowTemplate,
        step: WorkflowStep,
    ):

        workflow.add_step(step)

    def remove_step(
        self,
        workflow: WorkflowTemplate,
        step_id: str,
    ) -> bool:

        original = len(workflow.steps)

        workflow.steps = [

            step

            for step in workflow.steps

            if step.step_id != step_id

        ]

        return len(workflow.steps) != original

    def health(self):

        return {

            "service": "workflow_customization",

            "status": "healthy",

        }