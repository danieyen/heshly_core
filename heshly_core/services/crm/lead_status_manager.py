from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from heshly_core.models.crm import Lead, LeadStatus


@dataclass(slots=True)
class StatusChangeResult:
    lead_id: str
    previous_status: LeadStatus
    new_status: LeadStatus
    success: bool
    message: str
    changed_at: datetime = field(
        default_factory=datetime.utcnow
    )


class LeadStatusError(Exception):
    pass


class LeadStatusManager:
    """
    Manages lead lifecycle status changes.
    """

    VALID_TRANSITIONS = {
        LeadStatus.NEW: [
            LeadStatus.CONTACTED,
            LeadStatus.QUALIFIED,
            LeadStatus.UNQUALIFIED,
            LeadStatus.LOST,
        ],

        LeadStatus.CONTACTED: [
            LeadStatus.QUALIFIED,
            LeadStatus.UNQUALIFIED,
            LeadStatus.LOST,
        ],

        LeadStatus.QUALIFIED: [
            LeadStatus.CONVERTED,
            LeadStatus.LOST,
        ],

        LeadStatus.UNQUALIFIED: [
            LeadStatus.CONTACTED,
            LeadStatus.LOST,
        ],

        LeadStatus.CONVERTED: [],

        LeadStatus.LOST: [
            LeadStatus.CONTACTED,
        ],
    }


    def change_status(
        self,
        lead: Lead,
        new_status: LeadStatus,
    ) -> StatusChangeResult:

        if not lead.lead_id:
            raise LeadStatusError(
                "Lead ID is required."
            )

        current_status = lead.status


        if new_status not in self.VALID_TRANSITIONS[current_status]:

            raise LeadStatusError(
                f"Cannot change status from "
                f"{current_status.value} to "
                f"{new_status.value}"
            )


        lead.status = new_status
        lead.updated_at = datetime.utcnow()


        return StatusChangeResult(
            lead_id=lead.lead_id,
            previous_status=current_status,
            new_status=new_status,
            success=True,
            message="Lead status updated successfully.",
        )


    def convert(
        self,
        lead: Lead,
    ) -> StatusChangeResult:

        return self.change_status(
            lead,
            LeadStatus.CONVERTED,
        )


    def mark_lost(
        self,
        lead: Lead,
    ) -> StatusChangeResult:

        return self.change_status(
            lead,
            LeadStatus.LOST,
        )