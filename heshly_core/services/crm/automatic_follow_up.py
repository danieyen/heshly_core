from __future__ import annotations

from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


class AutomaticFollowUp:

    """
    Automatically creates follow-ups
    based on CRM events.
    """

    DEFAULT_RULES = {

        "lead_created": 1,

        "opportunity_created": 2,

        "quote_sent": 3,

        "appointment_completed": 7,

    }

    def __init__(
        self,
        scheduler: ReminderScheduler,
    ):

        self.scheduler = scheduler


    def create_follow_up(

        self,

        event: str,

        business_id: str,

        related_type: str,

        related_id: str,

        subject: str,

        assigned_to: str | None = None,

        follow_up_type: FollowUpType = (
            FollowUpType.CALL
        ),

    ) -> FollowUp:

        if event not in self.DEFAULT_RULES:

            raise ValueError(
                f"Unsupported event: {event}"
            )

        scheduled_for = (

            datetime.utcnow()

            + timedelta(
                days=self.DEFAULT_RULES[event]
            )

        )

        return self.scheduler.schedule(

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            follow_up_type=follow_up_type,

            scheduled_for=scheduled_for,

            subject=subject,

            assigned_to=assigned_to,

        )