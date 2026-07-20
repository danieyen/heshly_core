from heshly_core.models.workflow_template import (
    WorkflowStep,
)

from heshly_core.services.workflow.workflow_customization import (
    WorkflowCustomization,
)

from heshly_core.services.workflow.workflow_templates import (
    WorkflowTemplates,
)


def run_test():

    print("\n==============================")
    print("Workflow Customization Test")
    print("==============================\n")

    workflow = WorkflowTemplates().load(
        "dental"
    )

    service = WorkflowCustomization()

    assert service.rename_step(

        workflow,

        "2",

        "Patient Qualification",

    )

    print("✅ Rename step")

    assert workflow.steps[1].name == "Patient Qualification"

    assert service.disable_step(
        workflow,
        "4",
    )

    print("✅ Disable step")

    assert workflow.steps[3].enabled is False

    service.add_step(

        workflow,

        WorkflowStep(

            step_id="5",

            name="Collect Feedback",

            action="collect_feedback",

            order=5,

        ),

    )

    assert workflow.step_count == 5

    print("✅ Add step")

    assert service.remove_step(
        workflow,
        "5",
    )

    print("✅ Remove step")

    assert workflow.step_count == 4

    assert service.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 WORKFLOW CUSTOMIZATION TEST PASSED\n")


if __name__ == "__main__":

    run_test()