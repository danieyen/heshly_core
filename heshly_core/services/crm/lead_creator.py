from __future__ import annotations

import uuid
from datetime import datetime

from heshly_core.models.crm import Lead, LeadStatus
from heshly_core.services.crm.lead_validator import LeadValidator


class LeadCreationError(Exception):
    """Raised when lead creation fails."""
    pass


class LeadCreator:
    """
    Creates and validates Lead objects.
    """

    def __init__(self):
        self.validator = LeadValidator()

    def create(
        self,
        business_id: str,
        full_name: str,
        phone: str | None = None,
        email: str | None = None,
        company: str | None = None,
        source: str = "whatsapp",
    ) -> Lead:

        lead = Lead(
            lead_id=self._generate_id(),
            business_id=business_id,
            full_name=full_name,
            phone=phone,
            email=email,
            company=company,
            source=source,
            status=LeadStatus.NEW,
            score=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = self.validator.validate(lead)

        if not result.valid:
            raise LeadCreationError(
                f"Lead validation failed: {result.errors}"
            )

        return lead

    def _generate_id(self) -> str:
        """
        Generates unique lead ID.
        """

        return f"LEAD-{uuid.uuid4().hex[:8].upper()}"