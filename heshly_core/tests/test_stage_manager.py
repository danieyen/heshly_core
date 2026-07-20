from heshly_core.services.crm.stage_manager import (
    StageManager,
    StageManagementError,
)



def run():


    manager = StageManager()



    # Create stages

    new_stage = manager.create_stage(

        pipeline_id="PIPE-SALES",

        name="New Lead",

        order=1,

        probability=0.10,

    )


    qualified_stage = manager.create_stage(

        pipeline_id="PIPE-SALES",

        name="Qualified",

        order=2,

        probability=0.40,

    )


    proposal_stage = manager.create_stage(

        pipeline_id="PIPE-SALES",

        name="Proposal",

        order=3,

        probability=0.70,

    )


    print(new_stage)

    print(qualified_stage)

    print(proposal_stage)



    stages = manager.get_stages(
        "PIPE-SALES"
    )


    print("\nPipeline Stages:")

    for stage in stages:

        print(stage)



    assert len(stages) == 3

    assert stages[0].name == "New Lead"

    assert stages[2].name == "Proposal"



    # Invalid probability

    try:

        manager.create_stage(

            pipeline_id="PIPE-SALES",

            name="Invalid",

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