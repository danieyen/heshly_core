from heshly_core.models.crm import Opportunity

from heshly_core.services.crm.pipeline_manager import (
    PipelineManager,
)



def run():

    manager = PipelineManager()


    # Create pipeline

    pipeline = manager.create_pipeline(

        name="Dental Sales Pipeline",

        description="Dental customer journey",

        is_default=True,

    )


    print(
        "Pipeline:"
    )

    print(pipeline)



    assert pipeline.name == (
        "Dental Sales Pipeline"
    )



    # Create stages

    stage1 = manager.add_stage(

        pipeline_id=pipeline.pipeline_id,

        name="New Lead",

        order=1,

        probability=0.10,

    )


    stage2 = manager.add_stage(

        pipeline_id=pipeline.pipeline_id,

        name="Proposal",

        order=2,

        probability=0.70,

    )


    print("\nStages:")

    print(stage1)

    print(stage2)



    opportunities = [

        Opportunity(

            opportunity_id="OPP-001",

            lead_id="LEAD-001",

            title="Dental Implant",

            expected_value=200000,

            probability=0.70,

            pipeline_id=pipeline.pipeline_id,

            stage_id=stage2.stage_id,

        )

    ]



    # Metrics

    metrics = manager.get_metrics(

        pipeline.pipeline_id,

        opportunities,

    )


    print("\nMetrics:")

    print(metrics)


    assert metrics.total_value == 200000



    # Visualization

    view = manager.visualize(

        [stage1, stage2],

        opportunities,

    )


    print("\nVisualization:")

    for item in view:

        print(item)



    assert len(view) == 2



    print(
        "\n✅ Pipeline Manager Functional Test Passed"
    )



if __name__ == "__main__":
    run()