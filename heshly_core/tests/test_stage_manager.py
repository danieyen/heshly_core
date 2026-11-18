from heshly_core.services.crm.stage_manager import (
    StageManager,
    StageManagementError,
)
from heshly_core.services.crm.pipeline_definition_manager import (
    PipelineDefinitionManager,
)


def run():
    # Create a real pipeline first.
    pipeline_manager = PipelineDefinitionManager()

    pipeline = pipeline_manager.create_pipeline(
        name="Sales Pipeline",
        description="Stage Manager test pipeline",
    )

    pipeline_id = pipeline.pipeline_id

    print("Pipeline:")
    print(pipeline)

    manager = StageManager()

    # Create stages
    new_stage = manager.create_stage(
        pipeline_id=pipeline_id,
        name="New Lead",
        order=1,
        probability=0.10,
    )

    qualified_stage = manager.create_stage(
        pipeline_id=pipeline_id,
        name="Qualified",
        order=2,
        probability=0.40,
    )

    proposal_stage = manager.create_stage(
        pipeline_id=pipeline_id,
        name="Proposal",
        order=3,
        probability=0.70,
    )

    print("\nCreated Stages:")
    print(new_stage)
    print(qualified_stage)
    print(proposal_stage)

    stages = manager.get_stages(pipeline_id)

    print("\nPipeline Stages:")
    for stage in stages:
        print(stage)

    assert len(stages) == 3
    assert stages[0].name == "New Lead"
    assert stages[1].name == "Qualified"
    assert stages[2].name == "Proposal"

    # Invalid probability
    try:
        manager.create_stage(
            pipeline_id=pipeline_id,
            name="Invalid",
            order=4,
            probability=2,
        )

    except StageManagementError as error:
        print("\nExpected Error:")
        print(error)

    else:
        raise Exception(
            "Invalid stage should fail"
        )

    print(
        "\n✅ Stage Management Functional Test Passed"
    )


if __name__ == "__main__":
    run()
