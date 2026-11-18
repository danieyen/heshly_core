from heshly_core.models.crm import (
    Opportunity,
)

from heshly_core.services.crm.pipeline_metrics_manager import (
    PipelineMetricsManager,
)



def run():

    manager = PipelineMetricsManager()


    opportunities = [

        Opportunity(
            opportunity_id="OPP-001",
            lead_id="LEAD-001",
            tenant_id="heshly",
            title="Dental Treatment",
            expected_value=200000,
            probability=0.80,
            pipeline_id="SALES",
        ),


        Opportunity(
            opportunity_id="OPP-002",
            lead_id="LEAD-002",
            tenant_id="heshly",
            title="Website Project",
            expected_value=100000,
            probability=0.50,
            pipeline_id="SALES",
        ),


        Opportunity(
            opportunity_id="OPP-003",
            lead_id="LEAD-003",
            tenant_id="heshly",
            title="ERP Setup",
            expected_value=500000,
            probability=0.90,
            pipeline_id="ENTERPRISE",
        ),

    ]



    result = manager.calculate(

        pipeline_id="SALES",

        opportunities=opportunities,

    )


    print(result)


    assert result.opportunity_count == 2


    assert result.total_value == 300000


    assert result.weighted_value == 210000


    assert result.average_value == 150000



    print(
        "\n✅ Pipeline Metrics Functional Test Passed"
    )



if __name__ == "__main__":

    run()