from heshly_core.services.crm.stage_transition_manager import (
    StageTransitionManager,
    StageTransitionError,
)



def run():

    manager = StageTransitionManager()


    # Create allowed transitions

    manager.create_rule(
        pipeline_id="SALES",
        from_stage="NEW",
        to_stage="QUALIFIED",
    )


    manager.create_rule(
        pipeline_id="SALES",
        from_stage="QUALIFIED",
        to_stage="PROPOSAL",
    )


    # Valid transition

    result = manager.validate_transition(
        pipeline_id="SALES",
        from_stage="NEW",
        to_stage="QUALIFIED",
    )


    print(
        "Valid Transition:"
    )

    print(result)


    assert result is True



    # Invalid transition

    try:

        manager.validate_transition(
            pipeline_id="SALES",
            from_stage="NEW",
            to_stage="WON",
        )


    except StageTransitionError as error:

        print(
            "\nExpected Error:"
        )

        print(error)


    else:

        raise Exception(
            "Invalid transition should fail"
        )


    print(
        "\n✅ Stage Transition Rules Functional Test Passed"
    )



if __name__ == "__main__":

    run()