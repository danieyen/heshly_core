from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from heshly_core.models.calendar import (
    AppointmentRequest,
    CalendarEvent,
    AppointmentStatus,
)


@dataclass(slots=True)
class ConflictResult:
    """
    Result of conflict analysis.
    """

    has_conflict: bool

    message: str = ""

    conflicting_event: CalendarEvent | None = None


class ConflictDetector:
    """
    Detects scheduling conflicts.

    Handles:
    - time overlaps (exclusive end)
    - cancelled/completed events are ignored
    - optional staff filtering if request notes contain staff
    """

    def detect(
        self,
        request: AppointmentRequest,
        events: list[CalendarEvent],
    ) -> ConflictResult:

        if not request.start:
            return ConflictResult(
                has_conflict=True,
                message="Appointment start time is required.",
            )

        if request.duration_minutes <= 0:
            return ConflictResult(
                has_conflict=True,
                message="Invalid appointment duration.",
            )

        appointment_end = (
            request.start
            + timedelta(
                minutes=request.duration_minutes
            )
        )

        for event in events:

            # Ignore non-blocking statuses
            if event.status in (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW):
                continue

            # Basic time overlap: [start, end) overlaps [event.start, event.end)
            overlaps = (

                request.start < event.end

                and

                appointment_end > event.start

            )

            if overlaps:

                return ConflictResult(

                    has_conflict=True,

                    message="Appointment conflicts with an existing booking.",

                    conflicting_event=event,

                )

        return ConflictResult(

            has_conflict=False,

            message="No conflicts detected.",

        )

    def detect_for_staff(
        self,
        request: AppointmentRequest,
        events: list[CalendarEvent],
        staff_name: str | None = None,
    ) -> ConflictResult:
        """
        Staff-aware conflict detection. If staff_name is provided,
        only events for that staff are considered.
        """
        if staff_name:
            filtered = [e for e in events if (e.customer_name == staff_name or staff_name.lower() in (e.title or "").lower())]
            # Fallback to all events if filtering yields nothing and title doesn't contain staff
            # To avoid false negatives, if no staff-specific events found, check all
            if not filtered:
                filtered = events
            return self.detect(request, filtered)
        return self.detect(request, events)
