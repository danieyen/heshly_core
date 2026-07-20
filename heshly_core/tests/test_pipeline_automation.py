from heshly_core.services.crm.pipeline_automation import (
    PipelineAutomationManager,
    PipelineAutomationError,
)



def run():

    manager = PipelineAutomationManager()



    # Create automation rule

    rule = manager.create_rule(

        pipeline_id="PIPE-SALES",

        trigger_stage="QUALIFIED",

        action="Send WhatsApp Follow-up",

    )


    print("Created Rule:")
    print(rule)


    assert rule.pipeline_id == (
        "PIPE-SALES"
    )



    # Execute automation

    executions = manager.execute(

        opportunity_id="OPP-001",

        stage_id="QUALIFIED",

    )


    print("\nExecutions:")

    for execution in executions:

        print(execution)



    assert len(executions) == 1

    assert (
        executions[0].action
        ==
        "Send WhatsApp Follow-up"
    )



    # Invalid rule

    try:

        manager.create_rule(

            pipeline_id="",

            trigger_stage="QUALIFIED",

            action="Notify",

        )


    except PipelineAutomationError as error:

        print("\nExpected Error:")

        print(error)


    else:

        raise Exception(
            "Invalid automation should fail"
        )



    print(
        "\n✅ Pipeline Automation Functional Test Passed"
    )



if __name__ == "__main__":

    run()