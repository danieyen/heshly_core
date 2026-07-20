from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import Lead


@dataclass(slots=True)
class LeadScoreResult:
    lead_id: str
    previous_score: int
    new_score: int
    reason: str
    calculated_at: datetime = field(
        default_factory=datetime.utcnow
    )


class LeadScoringError(Exception):
    pass


class LeadScoringEngine:
    """
    Calculates and updates lead scores.
    """

    def calculate(
        self,
        lead: Lead,
    ) -> LeadScoreResult:

        if not lead.lead_id:
            raise LeadScoringError(
                "Lead ID is required."
            )

        previous_score = lead.score

        score = 0
        reasons = []

        # ------------------------------------------
        # Contact Information
        # ------------------------------------------

        if lead.phone:
            score += 20
            reasons.append(
                "Has phone number"
            )

        if lead.email:
            score += 10
            reasons.append(
                "Has email address"
            )

        # ------------------------------------------
        # Company Information
        # ------------------------------------------

        if lead.company:
            score += 10
            reasons.append(
                "Has company information"
            )

        # ------------------------------------------
        # Existing Qualification
        # ------------------------------------------

        if lead.status.value == "qualified":
            score += 40
            reasons.append(
                "Qualified lead"
            )

        # ------------------------------------------
        # Score Limit
        # ------------------------------------------

        score = min(score, 100)

        lead.score = score
        lead.updated_at = datetime.utcnow()

        return LeadScoreResult(
            lead_id=lead.lead_id,
            previous_score=previous_score,
            new_score=score,
            reason=", ".join(reasons),
        )