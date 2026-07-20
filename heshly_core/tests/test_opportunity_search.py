from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)

from heshly_core.services.crm.opportunity_search_engine import (
    OpportunitySearchEngine,
)



def run():

    engine = OpportunitySearchEngine()


    opportunities = [

        Opportunity(
            opportunity_id="OPP-001",
            lead_id="LEAD-001",
            title="Dental Implant Package",
            expected_value=200000,
            probability=0.80,
            pipeline_id="SALES",
            stage_id="PROPOSAL",
            status=OpportunityStatus.OPEN,
        ),


        Opportunity(
            opportunity_id="OPP-002",
            lead_id="LEAD-002",
            title="Website Development",
            expected_value=80000,
            probability=0.40,
            pipeline_id="SALES",
            stage_id="QUALIFIED",
            status=OpportunityStatus.OPEN,
        ),


        Opportunity(
            opportunity_id="OPP-003",
            lead_id="LEAD-003",
            title="ERP Implementation",
            expected_value=500000,
            probability=0.90,
            pipeline_id="ENTERPRISE",
            stage_id="NEGOTIATION",
            status=OpportunityStatus.WON,
        ),

    ]


    # Search title

    result = engine.search(
        opportunities,
        query="Dental",
    )

    print("Title Search:")
    print(result)

    assert len(result) == 1



    # Stage filter

    result = engine.search(
        opportunities,
        stage_id="PROPOSAL",
    )

    print("\nStage Search:")
    print(result)

    assert len(result) == 1



    # Value filter

    result = engine.search(
        opportunities,
        min_value=300000,
    )

    print("\nValue Search:")
    print(result)

    assert len(result) == 1



    # Probability filter

    result = engine.search(
        opportunities,
        min_probability=0.75,
    )

    print("\nProbability Search:")
    print(result)

    assert len(result) == 2



    print(
        "\n✅ Opportunity Search Functional Test Passed"
    )


if __name__ == "__main__":
    run()