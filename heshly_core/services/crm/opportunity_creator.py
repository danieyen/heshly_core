from __future__ import annotations

import uuid
from datetime import datetime

from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class OpportunityCreationError(Exception):
    pass


class OpportunityCreator:
    """
    Creates tenant-scoped Opportunity objects.

    tenant_id is always obtained from the active
    TenantContext. Callers must not supply an arbitrary
    tenant_id.
    """

    def __init__(self):
        self.context = TenantContext()

    def create(
        self,
        lead_id: str,
        title: str,
        expected_value: float = 0.0,
        pipeline_id: str | None = None,
        stage_id: str | None = None,
    ) -> Opportunity:

        if not lead_id.strip():
            raise OpportunityCreationError(
                "Lead ID is required."
            )

        if not title.strip():
            raise OpportunityCreationError(
                "Opportunity title is required."
            )

        if expected_value < 0:
            raise OpportunityCreationError(
                "Expected value cannot be negative."
            )

        tenant_id = self.context.require()

        now = datetime.utcnow()

        opportunity = Opportunity(
            opportunity_id=self._generate_id(),
            lead_id=lead_id,
            tenant_id=tenant_id,
            title=title,
            expected_value=expected_value,
            probability=0.10,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            status=OpportunityStatus.OPEN,
            created_at=now,
            updated_at=now,
        )

        return opportunity

    def _generate_id(self) -> str:
        return f"OPP-{uuid.uuid4().hex[:8].upper()}"
