from __future__ import annotations

from collections import Counter

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpStatus,
)


class FollowUpAnalytics:

    """
    Calculates analytics for Follow-ups.
    """

    def summary(
        self,
        follow_ups: list[FollowUp],
    ) -> dict:

        total = len(follow_ups)

        pending = sum(
            1
            for f in follow_ups
            if f.status == FollowUpStatus.PENDING
        )

        scheduled = sum(
            1
            for f in follow_ups
            if f.status == FollowUpStatus.SCHEDULED
        )

        completed = sum(
            1
            for f in follow_ups
            if f.status == FollowUpStatus.COMPLETED
        )

        cancelled = sum(
            1
            for f in follow_ups
            if f.status == FollowUpStatus.CANCELLED
        )

        missed = sum(
            1
            for f in follow_ups
            if f.status == FollowUpStatus.MISSED
        )

        overdue = sum(
            1
            for f in follow_ups
            if (
                f.status == FollowUpStatus.PENDING
                and f.scheduled_for < f.created_at
            )
        )

        completion_rate = (
            (completed / total) * 100
            if total > 0
            else 0.0
        )

        type_breakdown = Counter(
            f.follow_up_type.value
            for f in follow_ups
        )

        assignee_breakdown = Counter(
            f.assigned_to or "Unassigned"
            for f in follow_ups
        )

        return {

            "total": total,

            "pending": pending,

            "scheduled": scheduled,

            "completed": completed,

            "cancelled": cancelled,

            "missed": missed,

            "overdue": overdue,

            "completion_rate": round(
                completion_rate,
                2,
            ),

            "type_breakdown": dict(
                type_breakdown
            ),

            "assignee_breakdown": dict(
                assignee_breakdown
            ),
        }