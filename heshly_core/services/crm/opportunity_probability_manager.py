from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import Opportunity


@dataclass(slots=True)
class ProbabilityUpdateResult:
    opportunity_id: str

    previous_probability: float

    new_probability: float

    reason: str

    updated_at: datetime = field(
        default_factory=datetime.utcnow
    )


class OpportunityProbabilityError(Exception):
    pass


class OpportunityProbabilityManager:
    """
    Manages opportunity closing probability.
    """


    def update_probability(
        self,
        opportunity: Opportunity,
        probability: float,
        reason: str = "Manual update",
    ) -> ProbabilityUpdateResult:


        if not opportunity.opportunity_id:
            raise OpportunityProbabilityError(
                "Opportunity ID is required."
            )


        if probability < 0 or probability > 1:
            raise OpportunityProbabilityError(
                "Probability must be between 0 and 1."
            )


        previous_probability = (
            opportunity.probability
        )


        opportunity.probability = probability

        opportunity.updated_at = (
            datetime.utcnow()
        )


        return ProbabilityUpdateResult(
            opportunity_id=opportunity.opportunity_id,
            previous_probability=previous_probability,
            new_probability=probability,
            reason=reason,
        )