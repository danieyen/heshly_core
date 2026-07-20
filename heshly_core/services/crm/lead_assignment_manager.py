from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import Lead


@dataclass(slots=True)
class LeadAssignmentResult:
    success: bool
    lead_id: str
    assigned_to: str | None = None
    message: str = ""
    assigned_at: datetime = field(
        default_factory=datetime.utcnow
    )


class LeadAssignmentError(Exception):
    pass


class LeadAssignmentManager:
    """
    Handles lead ownership and assignment.
    """

    def assign(
        self,
        lead: Lead,
        assigned_to: str,
    ) -> LeadAssignmentResult:

        if not assigned_to.strip():
            raise LeadAssignmentError(
                "Assigned user cannot be empty."
            )

        if not lead.lead_id:
            raise LeadAssignmentError(
                "Lead ID is required."
            )

        lead.assigned_to = assigned_to
        lead.updated_at = datetime.utcnow()

        return LeadAssignmentResult(
            success=True,
            lead_id=lead.lead_id,
            assigned_to=assigned_to,
            message="Lead assigned successfully.",
        )


    def unassign(
        self,
        lead: Lead,
    ) -> LeadAssignmentResult:

        previous_owner = lead.assigned_to

        lead.assigned_to = None
        lead.updated_at = datetime.utcnow()

        return LeadAssignmentResult(
            success=True,
            lead_id=lead.lead_id,
            assigned_to=None,
            message=f"Lead removed from {previous_owner}.",
        )


    def reassign(
        self,
        lead: Lead,
        new_owner: str,
    ) -> LeadAssignmentResult:

        return self.assign(
            lead,
            new_owner,
        )