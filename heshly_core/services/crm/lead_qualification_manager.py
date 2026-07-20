from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import Lead, LeadStatus


@dataclass(slots=True)
class QualificationResult:
    lead_id: str
    qualified: bool
    confidence: float
    reason: str
    qualified_at: datetime = field(
        default_factory=datetime.utcnow
    )


class LeadQualificationError(Exception):
    pass


class LeadQualificationManager:
    """
    Handles lead qualification decisions.
    """

    def qualify(
        self,
        lead: Lead,
    ) -> QualificationResult:

        if not lead.lead_id:
            raise LeadQualificationError(
                "Lead ID is required."
            )

        # Basic qualification rules
        # Future versions will use AI scoring,
        # conversation history, and business rules.

        if lead.phone and lead.full_name:

            lead.status = LeadStatus.QUALIFIED
            lead.updated_at = datetime.utcnow()

            return QualificationResult(
                lead_id=lead.lead_id,
                qualified=True,
                confidence=0.90,
                reason="Lead has required contact information.",
            )

        else:

            lead.status = LeadStatus.UNQUALIFIED
            lead.updated_at = datetime.utcnow()

            return QualificationResult(
                lead_id=lead.lead_id,
                qualified=False,
                confidence=0.80,
                reason="Missing required contact information.",
            )