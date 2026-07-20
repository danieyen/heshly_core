from heshly_core.models.workflow_template import (
    WorkflowStep,
)

from heshly_core.services.workflow.workflow_manager import (
    WorkflowManager,
)


def run_test():

    print("\n==============================")
    print("Workflow Manager Test")
    print("==============================\n")

    manager = WorkflowManager()

    workflow = manager.assign_workflow(

        tenant_id="tenant_001",

        industry="dental",

    )

    assert workflow is not None

    print("✅ Workflow assigned")

    assert manager.rename_step(

        "tenant_001",

        "2",

        "Patient Assessment",

    )

    print("✅ Step renamed")

    manager.add_step(

        "tenant_001",

        WorkflowStep(

            step_id="5",

            name="Collect Feedback",

            action="collect_feedback",

            order=5,

        ),

    )

    print("✅ Step added")

    workflow = manager.workflow(
        "tenant_001"
    )

    assert workflow is not None
    assert workflow.step_count == 5

    print("✅ Workflow retrieved")

    history = manager.history(
        "tenant_001"
    )

    assert len(history) == 3

    print("✅ Version history")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 WORKFLOW MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()