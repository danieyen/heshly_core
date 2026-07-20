from heshly_core.services.workflow.workflow_assignment_manager import (
    WorkflowAssignmentManager,
)


def run_test():

    print("\n==============================")
    print("Workflow Assignment Test")
    print("==============================\n")

    manager = WorkflowAssignmentManager()

    assignment = manager.assign(

        tenant_id="tenant_001",

        industry="dental",

    )

    assert assignment.tenant_id == "tenant_001"

    print("✅ Assignment created")

    stored = manager.get(
        "tenant_001"
    )

    assert stored is not None

    print("✅ Assignment retrieved")

    assert stored.template.step_count == 4

    print("✅ Workflow copied")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 WORKFLOW ASSIGNMENT TEST PASSED\n")


if __name__ == "__main__":

    run_test()