from heshly_core.models.opportunity import (
    OpportunityStageChange,
    OpportunityValueUpdate,
    OpportunityActivity,
    OpportunityActivityType,
    OpportunityForecast,
    OpportunityFilter,
)


def run():

    # Stage Change

    stage_change = OpportunityStageChange(
        opportunity_id="OPP-001",
        previous_stage="Qualified",
        new_stage="Proposal",
    )

    print(stage_change)

    assert stage_change.new_stage == "Proposal"


    # Value Update

    value_update = OpportunityValueUpdate(
        opportunity_id="OPP-001",
        previous_value=20000,
        new_value=35000,
    )

    print(value_update)

    assert value_update.new_value == 35000


    # Activity

    activity = OpportunityActivity(
        activity_id="ACT-001",
        opportunity_id="OPP-001",
        activity_type=OpportunityActivityType.CREATED,
        description="Opportunity created from qualified lead.",
    )

    print(activity)

    assert activity.activity_type == OpportunityActivityType.CREATED


    # Forecast

    forecast = OpportunityForecast(
        opportunity_id="OPP-001",
        expected_value=100000,
        probability=0.75,
    )

    value = forecast.calculate()

    print(forecast)

    assert value == 75000


    # Filter

    filter = OpportunityFilter(
        stage_id="STAGE-001",
        min_value=50000,
    )

    print(filter)


    print(
        "\n✅ Opportunity Models Functional Test Passed"
    )


if __name__ == "__main__":
    run()