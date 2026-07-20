from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import (
    Opportunity,
    PipelineStage,
)


@dataclass(slots=True)
class StageChangeResult:
    opportunity_id: str

    previous_stage: str | None

    new_stage: str

    probability: float

    success: bool

    message: str

    changed_at: datetime = field(
        default_factory=datetime.utcnow
    )


class PipelineStageError(Exception):
    pass


class PipelineStageManager:
    """
    Manages opportunity pipeline stage changes.
    """


    def move_to_stage(
        self,
        opportunity: Opportunity,
        stage: PipelineStage,
    ) -> StageChangeResult:

        if not opportunity.opportunity_id:
            raise PipelineStageError(
                "Opportunity ID is required."
            )


        previous_stage = opportunity.stage_id


        opportunity.stage_id = stage.stage_id

        opportunity.pipeline_id = stage.pipeline_id

        opportunity.probability = stage.probability

        opportunity.updated_at = datetime.utcnow()


        return StageChangeResult(
            opportunity_id=opportunity.opportunity_id,
            previous_stage=previous_stage,
            new_stage=stage.stage_id,
            probability=stage.probability,
            success=True,
            message="Opportunity stage updated successfully.",
        )