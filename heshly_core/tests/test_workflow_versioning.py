from heshly_core.services.workflow.workflow_templates import (
    WorkflowTemplates,
)

from heshly_core.services.workflow.workflow_version_manager import (
    WorkflowVersionManager,
)


def run_test():

    print("\n==============================")
    print("Workflow Versioning Test")
    print("==============================\n")

    workflow = WorkflowTemplates().load(
        "dental"
    )

    manager = WorkflowVersionManager()

    v1 = manager.create_version(

        tenant_id="tenant_001",

        workflow=workflow,

        description="Initial version",

    )

    assert v1.version == 1

    print("✅ Version 1")

    workflow.steps[0].name = (
        "Receive WhatsApp Inquiry"
    )

    v2 = manager.create_version(

        tenant_id="tenant_001",

        workflow=workflow,

        description="Renamed first step",

    )

    assert v2.version == 2

    print("✅ Version 2")

    history = manager.history(
        "tenant_001"
    )

    assert len(history) == 2

    print("✅ Version history")

    latest = manager.latest(
        "tenant_001"
    )

    assert latest.version == 2

    print("✅ Latest version")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 WORKFLOW VERSIONING TEST PASSED\n")


if __name__ == "__main__":

    run_test()