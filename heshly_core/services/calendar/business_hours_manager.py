from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, UTC

from heshly_core.models.calendar import (
    AppointmentRequest,
)


@dataclass(slots=True)
class BusinessHours:
    """
    Business operating hours for a single day.
    For weekly schedules use heshly_core.models.calendar.BusinessHours
    with weekday field. This class is for single-day validation
    as called by n8n availability checks.
    """

    opening_time: time

    closing_time: time

    enabled: bool = True


@dataclass(slots=True)
class BusinessHoursResult:
    """
    Result of business hours validation.
    """

    within_hours: bool

    message: str = ""


class BusinessHoursManager:
    """
    Validates appointments against
    business operating hours.
    Handles timezone-aware datetimes and disabled days.
    """

    def is_within_hours(
        self,
        request: AppointmentRequest,
        hours: BusinessHours,
    ) -> BusinessHoursResult:
        """
        Check whether an appointment
        falls within business hours.
        """

        if not request.start:
            return BusinessHoursResult(
                within_hours=False,
                message="Appointment start time is required.",
            )

        if not hours.enabled:
            return BusinessHoursResult(
                within_hours=False,
                message="Business is closed on this day.",
            )

        if hours.opening_time >= hours.closing_time:
            return BusinessHoursResult(
                within_hours=False,
                message="Invalid business hours configuration.",
            )

        # Normalize to date of appointment
        # Use UTC if naive, preserve tz if aware
        start = request.start
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)

        appointment_end = (
            start
            + timedelta(
                minutes=request.duration_minutes
            )
        )

        # Build opening/closing on same date with same tz
        opening = datetime.combine(
            start.date(),
            hours.opening_time,
        ).replace(tzinfo=start.tzinfo)

        closing = datetime.combine(
            start.date(),
            hours.closing_time,
        ).replace(tzinfo=start.tzinfo)

        if start < opening:

            return BusinessHoursResult(

                within_hours=False,

                message="Appointment starts before business opens.",
            )

        if appointment_end > closing:

            return BusinessHoursResult(

                within_hours=False,

                message="Appointment ends after business closes.",
            )

        return BusinessHoursResult(

            within_hours=True,

            message="Appointment is within business hours.",
        )

    def validate_weekly(
        self,
        request: AppointmentRequest,
        weekly_hours: list,
    ) -> BusinessHoursResult:
        """
        Validate against weekly schedule (list of calendar.BusinessHours).
        """
        if not weekly_hours:
            return BusinessHoursResult(within_hours=True, message="No weekly hours configured.")

        weekday = request.start.weekday()
        for h in weekly_hours:
            if h.weekday == weekday:
                if not h.enabled:
                    return BusinessHoursResult(within_hours=False, message="Business is closed on this day.")
                # Map calendar.BusinessHours (opens_at/closes_at) to local BusinessHours
                return self.is_within_hours(
                    request,
                    BusinessHours(opening_time=h.opens_at, closing_time=h.closes_at, enabled=h.enabled),
                )
        return BusinessHoursResult(within_hours=False, message="No business hours defined for this weekday.")
