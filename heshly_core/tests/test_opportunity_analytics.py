from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)

from heshly_core.services.crm.opportunity_analytics import (
    OpportunityAnalytics,
)



def run():

    analytics = OpportunityAnalytics()


    opportunities = [

        Opportunity(
            opportunity_id="OPP-001",
            lead_id="LEAD-001",
            tenant_id="heshly",
            title="Dental Package",
            expected_value=200000,
            probability=0.80,
            status=OpportunityStatus.OPEN,
        ),


        Opportunity(
            opportunity_id="OPP-002",
            lead_id="LEAD-002",
            tenant_id="heshly",
            title="Website Project",
            expected_value=100000,
            probability=1.0,
            status=OpportunityStatus.WON,
        ),


        Opportunity(
            opportunity_id="OPP-003",
            lead_id="LEAD-003",
            tenant_id="heshly",
            title="ERP Setup",
            expected_value=300000,
            probability=0.0,
            status=OpportunityStatus.LOST,
        ),

    ]


    result = analytics.calculate(
        opportunities
    )


    print(result)


    assert result.total_opportunities == 3

    assert result.total_pipeline_value == 600000

    assert result.weighted_forecast == 260000

    assert result.won_count == 1

    assert result.lost_count == 1

    assert result.open_count == 1

    assert result.win_rate == 0.5


    print(
        "\n✅ Opportunity Analytics Functional Test Passed"
    )



if __name__ == "__main__":
    run()