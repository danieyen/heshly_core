from heshly_core.models.crm import (
    PipelineStage,
    OpportunityStatus,
)

from heshly_core.models.opportunity import (
    OpportunityActivityType,
)

from heshly_core.services.crm.opportunity_creator import (
    OpportunityCreator,
)

from heshly_core.services.crm.pipeline_stage_manager import (
    PipelineStageManager,
)

from heshly_core.services.crm.opportunity_probability_manager import (
    OpportunityProbabilityManager,
)

from heshly_core.services.crm.revenue_forecast_manager import (
    RevenueForecastManager,
)

from heshly_core.services.crm.opportunity_history_manager import (
    OpportunityHistoryManager,
)

from heshly_core.services.crm.opportunity_search_engine import (
    OpportunitySearchEngine,
)

from heshly_core.services.crm.opportunity_analytics import (
    OpportunityAnalytics,
)



def run():

    print(
        "=== Heshly CRM Opportunity Management Test ===\n"
    )


    # =====================================
    # 1. CREATE OPPORTUNITY
    # =====================================

    creator = OpportunityCreator()


    opportunity = creator.create(
        lead_id="LEAD-001",
        title="Dental Implant Package",
        expected_value=200000,
        pipeline_id="SALES",
        stage_id="NEW",
    )


    print("1. Opportunity Created")
    print(opportunity)


    assert opportunity.title == (
        "Dental Implant Package"
    )



    # =====================================
    # 2. PIPELINE STAGE CHANGE
    # =====================================

    stage_manager = PipelineStageManager()


    proposal_stage = PipelineStage(
        stage_id="PROPOSAL",
        pipeline_id="SALES",
        name="Proposal",
        order=3,
        probability=0.70,
    )


    stage_result = (
        stage_manager.move_to_stage(
            opportunity,
            proposal_stage,
        )
    )


    print("\n2. Stage Updated")
    print(stage_result)


    assert opportunity.stage_id == (
        "PROPOSAL"
    )



    # =====================================
    # 3. UPDATE PROBABILITY
    # =====================================

    probability_manager = (
        OpportunityProbabilityManager()
    )


    probability_result = (
        probability_manager.update_probability(
            opportunity,
            0.80,
            "Customer accepted quotation",
        )
    )


    print("\n3. Probability Updated")
    print(probability_result)


    assert opportunity.probability == 0.80



    # =====================================
    # 4. REVENUE FORECAST
    # =====================================

    forecast_manager = (
        RevenueForecastManager()
    )


    forecast = (
        forecast_manager.calculate(
            opportunity
        )
    )


    print("\n4. Revenue Forecast")
    print(forecast)


    assert forecast.forecast_value == 160000



    # =====================================
    # 5. HISTORY
    # =====================================

    history_manager = (
        OpportunityHistoryManager()
    )


    history_manager.add_activity(
        opportunity_id=opportunity.opportunity_id,
        activity_type=OpportunityActivityType.CREATED,
        description="Opportunity created.",
    )


    history_manager.add_activity(
        opportunity_id=opportunity.opportunity_id,
        activity_type=OpportunityActivityType.STAGE_CHANGED,
        description="Moved to proposal stage.",
    )


    history = (
        history_manager.get_history(
            opportunity.opportunity_id
        )
    )


    print("\n5. Opportunity History")
    print(history)


    assert len(history) == 2



    # =====================================
    # 6. SEARCH
    # =====================================

    search_engine = (
        OpportunitySearchEngine()
    )


    results = search_engine.search(
        [opportunity],
        query="Dental",
    )


    print("\n6. Search Results")
    print(results)


    assert len(results) == 1



    # =====================================
    # 7. ANALYTICS
    # =====================================

    analytics = (
        OpportunityAnalytics()
    )


    report = analytics.calculate(
        [opportunity]
    )


    print("\n7. Analytics")
    print(report)


    assert report.total_opportunities == 1

    assert report.total_pipeline_value == 200000

    assert report.weighted_forecast == 160000



    print(
        "\n================================="
    )

    print(
        "✅ Opportunity Management Functional Test Passed"
    )

    print(
        "================================="
    )



if __name__ == "__main__":
    run()