from __future__ import annotations

from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


class LostLeadRecovery:

    """
    Creates recovery follow-ups
    for inactive leads.
    """

    def __init__(
        self,
        scheduler: ReminderScheduler,
    ):

        self.scheduler = scheduler


    def recover(

        self,

        business_id: str,

        lead_id: str,

        customer_name: str,

        last_contact: datetime,

        assigned_to: str | None = None,

        inactivity_days: int = 30,

    ) -> FollowUp:

        days_since_contact = (
            datetime.utcnow() - last_contact
        ).days

        if days_since_contact < inactivity_days:

            raise ValueError(
                "Lead has not been inactive long enough."
            )

        return self.scheduler.schedule(

            business_id=business_id,

            related_type="lead",

            related_id=lead_id,

            follow_up_type=FollowUpType.WHATSAPP,

            scheduled_for=(
                datetime.utcnow()
                + timedelta(hours=1)
            ),

            subject=f"Recover lost lead: {customer_name}",

            description=(
                f"No contact for "
                f"{days_since_contact} days."
            ),

            assigned_to=assigned_to,

        )