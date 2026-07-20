from heshly_core.models.crm import (
    Pipeline,
    PipelineStage,
)

from heshly_core.models.pipeline import (
    PipelineMetrics,
    PipelineStageSummary,
)


def run():


    pipeline = Pipeline(
        pipeline_id="SALES",
        name="Sales Pipeline",
        description="Main sales process",
        is_default=True,
    )


    print(pipeline)


    assert pipeline.name == (
        "Sales Pipeline"
    )


    stage = PipelineStage(
        stage_id="QUALIFIED",
        pipeline_id="SALES",
        name="Qualified",
        order=2,
        probability=0.40,
    )


    print(stage)


    assert stage.probability == 0.40



    metrics = PipelineMetrics(
        pipeline_id="SALES",
        total_opportunities=10,
        total_value=1000000,
        weighted_value=500000,
    )


    print(metrics)


    assert metrics.total_value == 1000000



    summary = PipelineStageSummary(
        stage_id="QUALIFIED",
        stage_name="Qualified",
        opportunity_count=5,
        total_value=500000,
        probability=0.40,
    )


    print(summary)


    assert summary.stage_name == "Qualified"


    print(
        "\n✅ Pipeline Models Functional Test Passed"
    )


if __name__ == "__main__":
    run()