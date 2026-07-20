from __future__ import annotations

from dataclasses import dataclass

from heshly_core.models.crm import (
    Opportunity,
    PipelineStage,
)


@dataclass(slots=True)
class PipelineStageView:

    stage_id: str

    stage_name: str

    order: int

    opportunity_count: int

    total_value: float

    weighted_value: float



class PipelineVisualizationError(Exception):
    pass



class PipelineVisualizationManager:
    """
    Converts pipeline data into dashboard format.
    """


    def build_view(
        self,
        stages: list[PipelineStage],
        opportunities: list[Opportunity],
    ) -> list[PipelineStageView]:


        if stages is None:

            raise PipelineVisualizationError(
                "Stages are required."
            )


        if opportunities is None:

            raise PipelineVisualizationError(
                "Opportunities are required."
            )


        views = []


        for stage in sorted(
            stages,
            key=lambda x: x.order
        ):


            stage_opportunities = [

                opportunity

                for opportunity in opportunities

                if opportunity.stage_id
                == stage.stage_id

            ]


            total_value = sum(

                opportunity.expected_value

                for opportunity in stage_opportunities

            )


            weighted_value = sum(

                opportunity.expected_value
                *
                opportunity.probability

                for opportunity in stage_opportunities

            )


            views.append(

                PipelineStageView(

                    stage_id=stage.stage_id,

                    stage_name=stage.name,

                    order=stage.order,

                    opportunity_count=len(
                        stage_opportunities
                    ),

                    total_value=total_value,

                    weighted_value=weighted_value,

                )

            )


        return views