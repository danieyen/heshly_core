from heshly_core.services.crm.pipeline_definition_manager import (
    PipelineDefinitionManager,
    PipelineDefinitionError,
)


def run():


    manager = PipelineDefinitionManager()


    # Create Pipeline

    pipeline = manager.create_pipeline(

        name="Dental Sales Pipeline",

        description="Pipeline for dental appointments and treatments",

        is_default=True,

    )


    print("Created Pipeline:")
    print(pipeline)


    assert pipeline.pipeline_id.startswith(
        "PIPE-"
    )


    assert pipeline.name == (
        "Dental Sales Pipeline"
    )


    assert pipeline.is_default is True



    # Invalid Pipeline

    try:

        manager.create_pipeline(
            name=""
        )


    except PipelineDefinitionError as error:

        print("\nExpected Error:")
        print(error)


    else:

        raise Exception(
            "Invalid pipeline should fail"
        )



    print(
        "\n✅ Pipeline Definition Functional Test Passed"
    )



if __name__ == "__main__":
    run()