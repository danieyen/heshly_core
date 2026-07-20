from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import time
from datetime import timedelta

from heshly_core.models.calendar import (
    AppointmentRequest,
)


@dataclass(slots=True)
class BusinessHours:
    """
    Business operating hours.
    """

    opening_time: time

    closing_time: time


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

        appointment_end = (
            request.start
            + timedelta(
                minutes=request.duration_minutes
            )
        )

        opening = datetime.combine(
            request.start.date(),
            hours.opening_time,
        )

        closing = datetime.combine(
            request.start.date(),
            hours.closing_time,
        )

        if request.start < opening:

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