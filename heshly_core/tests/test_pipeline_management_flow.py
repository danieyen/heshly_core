from heshly_core.models.crm import (
    Opportunity,
)

from heshly_core.services.crm.pipeline_manager import (
    PipelineManager,
)

from heshly_core.services.crm.stage_transition_manager import (
    StageTransitionManager,
)



def run():

    print(
        "=== Heshly CRM Pipeline Management Test ===\n"
    )


    manager = PipelineManager()


    # =====================================
    # 1. CREATE PIPELINE
    # =====================================

    pipeline = manager.create_pipeline(

        name="Dental Sales Pipeline",

        description="Customer acquisition pipeline",

        is_default=True,

    )


    print("1. Pipeline Created")
    print(pipeline)


    assert pipeline.name == (
        "Dental Sales Pipeline"
    )



    # =====================================
    # 2. CREATE STAGES
    # =====================================

    new_stage = manager.add_stage(

        pipeline_id=pipeline.pipeline_id,

        name="New Lead",

        order=1,

        probability=0.10,

    )


    qualified_stage = manager.add_stage(

        pipeline_id=pipeline.pipeline_id,

        name="Qualified",

        order=2,

        probability=0.40,

    )


    proposal_stage = manager.add_stage(

        pipeline_id=pipeline.pipeline_id,

        name="Proposal",

        order=3,

        probability=0.70,

    )


    print("\n2. Stages Created")

    print(new_stage)

    print(qualified_stage)

    print(proposal_stage)


    assert proposal_stage.name == "Proposal"



    # =====================================
    # 3. STAGE TRANSITION RULES
    # =====================================

    transition = StageTransitionManager()


    transition.create_rule(

        pipeline_id=pipeline.pipeline_id,

        from_stage=new_stage.stage_id,

        to_stage=qualified_stage.stage_id,

    )


    allowed = transition.can_transition(

        pipeline.pipeline_id,

        new_stage.stage_id,

        qualified_stage.stage_id,

    )


    print("\n3. Transition Validation")

    print(allowed)


    assert allowed is True



    # =====================================
    # 4. CREATE OPPORTUNITY
    # =====================================

    opportunity = Opportunity(

        opportunity_id="OPP-001",

        lead_id="LEAD-001",

        title="Dental Implant Package",

        expected_value=250000,

        probability=0.40,

        pipeline_id=pipeline.pipeline_id,

        stage_id=qualified_stage.stage_id,

    )


    print("\n4. Opportunity Added")

    print(opportunity)



    # =====================================
    # 5. PIPELINE METRICS
    # =====================================

    metrics = manager.get_metrics(

        pipeline.pipeline_id,

        [opportunity],

    )


    print("\n5. Pipeline Metrics")

    print(metrics)


    assert metrics.total_value == 250000

    assert metrics.weighted_value == 100000



    # =====================================
    # 6. PIPELINE VISUALIZATION
    # =====================================

    visualization = manager.visualize(

        [
            new_stage,
            qualified_stage,
            proposal_stage,
        ],

        [
            opportunity
        ],

    )


    print("\n6. Pipeline Visualization")


    for item in visualization:

        print(item)



    assert len(visualization) == 3



    print(
        "\n================================="
    )

    print(
        "✅ Pipeline Management Functional Test Passed"
    )

    print(
        "================================="
    )



if __name__ == "__main__":

    run()