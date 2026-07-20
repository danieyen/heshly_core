from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import Opportunity


@dataclass(slots=True)
class RevenueForecastResult:
    opportunity_id: str

    expected_value: float

    probability: float

    forecast_value: float

    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )


class RevenueForecastError(Exception):
    pass


class RevenueForecastManager:
    """
    Calculates opportunity revenue forecasts.
    """


    def calculate(
        self,
        opportunity: Opportunity,
    ) -> RevenueForecastResult:


        if not opportunity.opportunity_id:
            raise RevenueForecastError(
                "Opportunity ID is required."
            )


        if opportunity.expected_value < 0:
            raise RevenueForecastError(
                "Expected value cannot be negative."
            )


        if (
            opportunity.probability < 0
            or opportunity.probability > 1
        ):
            raise RevenueForecastError(
                "Probability must be between 0 and 1."
            )


        forecast_value = (
            opportunity.expected_value
            *
            opportunity.probability
        )


        return RevenueForecastResult(
            opportunity_id=opportunity.opportunity_id,
            expected_value=opportunity.expected_value,
            probability=opportunity.probability,
            forecast_value=forecast_value,
        )