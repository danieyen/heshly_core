from __future__ import annotations

import uuid

from datetime import datetime

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpStatus,
    FollowUpType,
)


class ReminderSchedulerError(Exception):
    pass


class ReminderScheduler:

    def __init__(self):

        self.follow_ups: list[FollowUp] = []


    def schedule(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        follow_up_type: FollowUpType,
        scheduled_for: datetime,
        subject: str,
        description: str | None = None,
        assigned_to: str | None = None,
    ) -> FollowUp:

        if not business_id:
            raise ReminderSchedulerError(
                "Business ID is required."
            )

        if scheduled_for <= datetime.utcnow():
            raise ReminderSchedulerError(
                "Scheduled time must be in the future."
            )

        follow_up = FollowUp(

            follow_up_id=self._generate_id(),

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            follow_up_type=follow_up_type,

            scheduled_for=scheduled_for,

            subject=subject,

            description=description,

            assigned_to=assigned_to,

        )

        self.follow_ups.append(follow_up)

        return follow_up


    def due_reminders(
        self,
        current_time: datetime,
    ) -> list[FollowUp]:

        return [

            follow_up

            for follow_up in self.follow_ups

            if (
                follow_up.status == FollowUpStatus.PENDING
                and
                follow_up.scheduled_for <= current_time
            )

        ]


    def overdue(
        self,
        current_time: datetime,
    ) -> list[FollowUp]:

        return self.due_reminders(current_time)


    def complete(
        self,
        follow_up_id: str,
    ) -> FollowUp:

        for follow_up in self.follow_ups:

            if follow_up.follow_up_id == follow_up_id:

                follow_up.status = (
                    FollowUpStatus.COMPLETED
                )

                follow_up.completed_at = (
                    datetime.utcnow()
                )

                return follow_up

        raise ReminderSchedulerError(
            "Follow-up not found."
        )


    def _generate_id(self):

        return (
            f"FU-{uuid.uuid4().hex[:8].upper()}"
        )