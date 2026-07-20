from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from heshly_core.models.calendar import (
    AppointmentRequest,
    CalendarEvent,
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

    Future versions will support:

    - staff conflicts
    - room conflicts
    - equipment conflicts
    - travel buffers
    - business policies
    """

    def detect(
        self,
        request: AppointmentRequest,
        events: list[CalendarEvent],
    ) -> ConflictResult:

        appointment_end = (
            request.start
            + timedelta(
                minutes=request.duration_minutes
            )
        )

        for event in events:

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