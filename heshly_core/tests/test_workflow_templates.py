from heshly_core.services.workflow.workflow_templates import (
    WorkflowTemplates,
)


def run_test():

    print("\n==============================")
    print("Workflow Templates Test")
    print("==============================\n")

    templates = WorkflowTemplates()

    dental = templates.load("dental")

    assert dental.step_count == 4

    print("✅ Dental workflow")

    salon = templates.load("salon")

    assert salon.step_count == 3

    print("✅ Salon workflow")

    insurance = templates.load("insurance")

    assert insurance.step_count == 3

    print("✅ Insurance workflow")

    logistics = templates.load("logistics")

    assert logistics.step_count == 3

    print("✅ Logistics workflow")

    print("\n🎉 WORKFLOW TEMPLATE TEST PASSED\n")


if __name__ == "__main__":

    run_test()