from __future__ import annotations

from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


class MissedAppointmentRecovery:

    """
    Creates automatic recovery follow-ups
    for missed appointments.
    """

    def __init__(
        self,
        scheduler: ReminderScheduler,
    ):

        self.scheduler = scheduler


    def recover(

        self,

        business_id: str,

        appointment_id: str,

        customer_name: str,

        assigned_to: str | None = None,

    ) -> FollowUp:

        return self.scheduler.schedule(

            business_id=business_id,

            related_type="appointment",

            related_id=appointment_id,

            follow_up_type=FollowUpType.WHATSAPP,

            scheduled_for=(
                datetime.utcnow()
                + timedelta(hours=2)
            ),

            subject=f"Recover missed appointment for {customer_name}",

            description=(
                "Customer missed the appointment. "
                "Contact customer and offer to reschedule."
            ),

            assigned_to=assigned_to,

        )