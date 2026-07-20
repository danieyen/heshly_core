from __future__ import annotations

from dataclasses import dataclass

from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)


@dataclass(slots=True)
class OpportunityAnalyticsResult:

    total_opportunities: int

    total_pipeline_value: float

    weighted_forecast: float

    average_value: float

    won_count: int

    lost_count: int

    open_count: int

    win_rate: float



class OpportunityAnalyticsError(Exception):
    pass



class OpportunityAnalytics:

    """
    Calculates opportunity pipeline analytics.
    """


    def calculate(
        self,
        opportunities: list[Opportunity],
    ) -> OpportunityAnalyticsResult:


        if opportunities is None:

            raise OpportunityAnalyticsError(
                "Opportunity list is required."
            )


        total = len(opportunities)


        if total == 0:

            return OpportunityAnalyticsResult(
                total_opportunities=0,
                total_pipeline_value=0,
                weighted_forecast=0,
                average_value=0,
                won_count=0,
                lost_count=0,
                open_count=0,
                win_rate=0,
            )


        total_value = sum(
            opportunity.expected_value
            for opportunity in opportunities
        )


        weighted_forecast = sum(
            opportunity.expected_value
            *
            opportunity.probability
            for opportunity in opportunities
        )


        average_value = (
            total_value / total
        )


        won = len(
            [
                opportunity
                for opportunity in opportunities
                if opportunity.status
                == OpportunityStatus.WON
            ]
        )


        lost = len(
            [
                opportunity
                for opportunity in opportunities
                if opportunity.status
                == OpportunityStatus.LOST
            ]
        )


        open_count = len(
            [
                opportunity
                for opportunity in opportunities
                if opportunity.status
                == OpportunityStatus.OPEN
            ]
        )


        closed = won + lost


        win_rate = (
            won / closed
            if closed > 0
            else 0
        )


        return OpportunityAnalyticsResult(

            total_opportunities=total,

            total_pipeline_value=total_value,

            weighted_forecast=weighted_forecast,

            average_value=average_value,

            won_count=won,

            lost_count=lost,

            open_count=open_count,

            win_rate=win_rate,
        )