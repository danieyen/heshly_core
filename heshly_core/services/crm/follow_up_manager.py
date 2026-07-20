from __future__ import annotations

from datetime import datetime

from heshly_core.models.follow_up import (
    FollowUpType,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)

from heshly_core.services.crm.automatic_follow_up import (
    AutomaticFollowUp,
)

from heshly_core.services.crm.escalation_rules import (
    EscalationRules,
)

from heshly_core.services.crm.missed_appointment_recovery import (
    MissedAppointmentRecovery,
)

from heshly_core.services.crm.lost_lead_recovery import (
    LostLeadRecovery,
)

from heshly_core.services.crm.follow_up_analytics import (
    FollowUpAnalytics,
)


class FollowUpManager:

    """
    Central Follow-up orchestration service.
    """

    def __init__(self):

        self.scheduler = ReminderScheduler()

        self.automatic = AutomaticFollowUp(
            self.scheduler
        )

        self.escalation = EscalationRules()

        self.missed_recovery = (
            MissedAppointmentRecovery(
                self.scheduler
            )
        )

        self.lost_recovery = (
            LostLeadRecovery(
                self.scheduler
            )
        )

        self.analytics = (
            FollowUpAnalytics()
        )

    # ----------------------------------------
    # Scheduler
    # ----------------------------------------

    def schedule(self, **kwargs):

        return self.scheduler.schedule(
            **kwargs
        )

    # ----------------------------------------
    # Automatic Follow-up
    # ----------------------------------------

    def create_automatic(
        self,
        **kwargs,
    ):

        return self.automatic.create_follow_up(
            **kwargs
        )

    # ----------------------------------------
    # Missed Appointment
    # ----------------------------------------

    def recover_missed_appointment(
        self,
        **kwargs,
    ):

        return self.missed_recovery.recover(
            **kwargs
        )

    # ----------------------------------------
    # Lost Lead
    # ----------------------------------------

    def recover_lost_lead(
        self,
        **kwargs,
    ):

        return self.lost_recovery.recover(
            **kwargs
        )

    # ----------------------------------------
    # Escalation
    # ----------------------------------------

    def evaluate_escalation(

        self,

        follow_up,

        current_time=None,

    ):

        if current_time is None:

            current_time = datetime.utcnow()

        return self.escalation.evaluate(

            follow_up,

            current_time,

        )

    # ----------------------------------------
    # Analytics
    # ----------------------------------------

    def analytics_summary(self):

        return self.analytics.summary(

            self.scheduler.follow_ups

        )

    # ----------------------------------------
    # Due Reminders
    # ----------------------------------------

    def due_reminders(

        self,

        current_time=None,

    ):

        if current_time is None:

            current_time = datetime.utcnow()

        return self.scheduler.due_reminders(

            current_time

        )

    # ----------------------------------------
    # Complete Follow-up
    # ----------------------------------------

    def complete(

        self,

        follow_up_id,

    ):

        return self.scheduler.complete(

            follow_up_id

        )