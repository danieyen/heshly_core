from heshly_core.models.opportunity import (
    OpportunityActivityType,
)

from heshly_core.services.crm.opportunity_history_manager import (
    OpportunityHistoryManager,
    OpportunityHistoryError,
)



def run():

    manager = OpportunityHistoryManager()


    # Add creation activity

    activity1 = manager.add_activity(
        opportunity_id="OPP-001",
        activity_type=OpportunityActivityType.CREATED,
        description="Opportunity created from qualified lead.",
        created_by="AI Receptionist",
    )


    print(activity1)


    # Add stage change

    activity2 = manager.add_activity(
        opportunity_id="OPP-001",
        activity_type=OpportunityActivityType.STAGE_CHANGED,
        description="Moved from Qualified to Proposal.",
        created_by="Sales Agent",
    )


    print(activity2)



    # Retrieve history

    history = manager.get_history(
        "OPP-001"
    )


    print("\nOpportunity History:")
    
    for item in history:
        print(item)


    assert len(history) == 2



    # Invalid test

    try:

        manager.add_activity(
            opportunity_id="",
            activity_type=OpportunityActivityType.CREATED,
            description="Test",
        )


    except OpportunityHistoryError as error:

        print("\nExpected Error:")
        print(error)


    else:

        raise Exception(
            "Invalid history entry should fail"
        )


    print(
        "\n✅ Opportunity History Functional Test Passed"
    )



if __name__ == "__main__":
    run()