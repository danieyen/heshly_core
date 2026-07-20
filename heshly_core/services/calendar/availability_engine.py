from __future__ import annotations

from datetime import datetime, timedelta

from heshly_core.models.calendar import (
    AvailabilityRequest,
    AvailabilityResult,
    CalendarEvent,
    TimeSlot,
)


class AvailabilityEngine:
    """
    Determines appointment availability.

    This engine answers scheduling questions
    but does not create appointments.
    """

    def is_available(
        self,
        start: datetime,
        duration_minutes: int,
        events: list[CalendarEvent],
    ) -> bool:
        """
        Returns True if the requested time
        does not overlap an existing event.
        """

        end = start + timedelta(
            minutes=duration_minutes
        )

        for event in events:

            if (
                start < event.end
                and end > event.start
            ):
                return False

        return True

    def find_available_slots(
        self,
        request: AvailabilityRequest,
        events: list[CalendarEvent],
        working_start: datetime,
        working_end: datetime,
        interval_minutes: int = 30,
    ) -> AvailabilityResult:
        """
        Returns all available slots within
        the specified working period.
        """

        slots: list[TimeSlot] = []

        current = working_start

        duration = timedelta(
            minutes=request.duration_minutes
        )

        interval = timedelta(
            minutes=interval_minutes
        )

        while current + duration <= working_end:

            if self.is_available(
                current,
                request.duration_minutes,
                events,
            ):

                slots.append(

                    TimeSlot(

                        start=current,

                        end=current + duration,

                        available=True,
                    )

                )

            current += interval

        return AvailabilityResult(

            available=len(slots) > 0,

            slots=slots,
        )

    def next_available_slot(
        self,
        request: AvailabilityRequest,
        events: list[CalendarEvent],
        working_start: datetime,
        working_end: datetime,
    ) -> TimeSlot | None:
        """
        Returns the first available slot.
        """

        result = self.find_available_slots(

            request=request,

            events=events,

            working_start=working_start,

            working_end=working_end,

            interval_minutes=30,
        )

        if result.slots:

            return result.slots[0]

        return None