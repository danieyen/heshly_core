from heshly_core.models.crm import (
    Opportunity,
    PipelineStage,
)

from heshly_core.services.crm.pipeline_stage_manager import (
    PipelineStageManager,
)


def run():

    manager = PipelineStageManager()


    opportunity = Opportunity(
        opportunity_id="OPP-001",
        lead_id="LEAD-001",
        title="Dental Implant Package",
    )


    qualified_stage = PipelineStage(
        stage_id="QUALIFIED",
        pipeline_id="SALES",
        name="Qualified",
        order=2,
        probability=0.40,
    )


    result = manager.move_to_stage(
        opportunity,
        qualified_stage,
    )


    print(result)


    assert opportunity.stage_id == (
        "QUALIFIED"
    )

    assert opportunity.probability == 0.40


    proposal_stage = PipelineStage(
        stage_id="PROPOSAL",
        pipeline_id="SALES",
        name="Proposal",
        order=3,
        probability=0.70,
    )


    result = manager.move_to_stage(
        opportunity,
        proposal_stage,
    )


    print(result)


    assert opportunity.stage_id == (
        "PROPOSAL"
    )

    assert opportunity.probability == 0.70


    print(
        "\n✅ Pipeline Stage Management Functional Test Passed"
    )


if __name__ == "__main__":
    run()