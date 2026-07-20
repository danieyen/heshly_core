from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpStatus,
)


class EscalationAction(str, Enum):

    NONE = "none"

    REMIND_ASSIGNEE = "remind_assignee"

    REASSIGN = "reassign"

    NOTIFY_MANAGER = "notify_manager"

    ESCALATE_TO_HUMAN = "escalate_to_human"


@dataclass(slots=True)
class EscalationResult:

    escalated: bool

    action: EscalationAction

    reason: str


class EscalationRules:

    """
    Determines what should happen
    when a follow-up becomes overdue.
    """

    def evaluate(
        self,
        follow_up: FollowUp,
        current_time: datetime,
    ) -> EscalationResult:

        if follow_up.status == FollowUpStatus.COMPLETED:

            return EscalationResult(

                escalated=False,

                action=EscalationAction.NONE,

                reason="Follow-up already completed.",

            )

        if current_time <= follow_up.scheduled_for:

            return EscalationResult(

                escalated=False,

                action=EscalationAction.NONE,

                reason="Follow-up is not overdue.",

            )

        overdue_days = (
            current_time - follow_up.scheduled_for
        ).days

        if overdue_days >= 7:

            return EscalationResult(

                escalated=True,

                action=EscalationAction.ESCALATE_TO_HUMAN,

                reason="Overdue for more than 7 days.",

            )

        if overdue_days >= 3:

            return EscalationResult(

                escalated=True,

                action=EscalationAction.NOTIFY_MANAGER,

                reason="Overdue for more than 3 days.",

            )

        return EscalationResult(

            escalated=True,

            action=EscalationAction.REMIND_ASSIGNEE,

            reason="Follow-up is overdue.",

        )