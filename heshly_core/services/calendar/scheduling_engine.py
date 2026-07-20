from __future__ import annotations

from heshly_core.models.calendar import (
    AppointmentRequest,
    AppointmentResult,
    AvailabilityRequest,
)

from heshly_core.services.calendar.appointment_manager import (
    AppointmentManager,
)

from heshly_core.services.calendar.availability_engine import (
    AvailabilityEngine,
)


class SchedulingEngine:
    """
    Coordinates appointment scheduling.

    The scheduling engine determines whether
    an appointment can be booked before
    delegating creation to the
    AppointmentManager.
    """

    def __init__(
        self,
        availability_engine: AvailabilityEngine | None = None,
        appointment_manager: AppointmentManager | None = None,
    ) -> None:

        self._availability = (
            availability_engine
            or AvailabilityEngine()
        )

        self._appointments = (
            appointment_manager
            or AppointmentManager()
        )

    def schedule(
        self,
        request: AppointmentRequest,
        events,
    ) -> AppointmentResult:
        """
        Schedule an appointment if the
        requested slot is available.
        """

        available = self._availability.is_available(

            start=request.start,

            duration_minutes=request.duration_minutes,

            events=events,
        )

        if not available:

            return AppointmentResult(

                success=False,

                appointment_id=None,

                status=None,

                message="Requested time is unavailable.",
            )

        return self._appointments.create(
            request
        )

    def check_availability(
        self,
        request: AvailabilityRequest,
        events,
        working_start,
        working_end,
    ):

        return self._availability.find_available_slots(

            request=request,

            events=events,

            working_start=working_start,

            working_end=working_end,
        )