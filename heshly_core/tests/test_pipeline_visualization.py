from heshly_core.models.crm import (
    PipelineStage,
    Opportunity,
)

from heshly_core.services.crm.pipeline_visualization import (
    PipelineVisualizationManager,
)



def run():

    manager = PipelineVisualizationManager()


    stages = [

        PipelineStage(
            stage_id="NEW",
            pipeline_id="SALES",
            name="New Lead",
            order=1,
            probability=0.10,
        ),


        PipelineStage(
            stage_id="PROPOSAL",
            pipeline_id="SALES",
            name="Proposal",
            order=2,
            probability=0.70,
        ),

    ]



    opportunities = [

        Opportunity(
            opportunity_id="OPP-001",
            lead_id="LEAD-001",
            title="Dental Package",
            expected_value=200000,
            probability=0.70,
            stage_id="PROPOSAL",
        ),


        Opportunity(
            opportunity_id="OPP-002",
            lead_id="LEAD-002",
            title="Website",
            expected_value=100000,
            probability=0.10,
            stage_id="NEW",
        ),

    ]



    view = manager.build_view(
        stages,
        opportunities,
    )


    print("\nPipeline Visualization:")

    for item in view:

        print(item)



    assert len(view) == 2


    assert view[0].stage_name == (
        "New Lead"
    )


    assert view[0].total_value == 100000


    assert view[1].total_value == 200000



    print(
        "\n✅ Pipeline Visualization Functional Test Passed"
    )



if __name__ == "__main__":
    run()