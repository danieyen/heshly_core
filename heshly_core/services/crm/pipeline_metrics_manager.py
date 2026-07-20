from __future__ import annotations

from dataclasses import dataclass

from heshly_core.models.crm import Opportunity


@dataclass(slots=True)
class PipelineMetricsResult:

    pipeline_id: str

    opportunity_count: int

    total_value: float

    weighted_value: float

    average_value: float



class PipelineMetricsError(Exception):
    pass



class PipelineMetricsManager:
    """
    Calculates pipeline performance metrics.
    """


    def calculate(
        self,
        pipeline_id: str,
        opportunities: list[Opportunity],
    ) -> PipelineMetricsResult:


        if not pipeline_id:

            raise PipelineMetricsError(
                "Pipeline ID is required."
            )


        if opportunities is None:

            raise PipelineMetricsError(
                "Opportunity list is required."
            )


        pipeline_opportunities = [

            opportunity

            for opportunity in opportunities

            if opportunity.pipeline_id
            == pipeline_id

        ]


        count = len(
            pipeline_opportunities
        )


        total_value = sum(

            opportunity.expected_value

            for opportunity in pipeline_opportunities

        )


        weighted_value = sum(

            opportunity.expected_value
            *
            opportunity.probability

            for opportunity in pipeline_opportunities

        )


        average_value = (

            total_value / count

            if count > 0

            else 0

        )


        return PipelineMetricsResult(

            pipeline_id=pipeline_id,

            opportunity_count=count,

            total_value=total_value,

            weighted_value=weighted_value,

            average_value=average_value,

        )