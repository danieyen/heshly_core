from __future__ import annotations

from heshly_core.models.calendar import (
    AppointmentRequest,
    AvailabilityRequest,
)

from heshly_core.services.calendar.business_hours_manager import (
    BusinessHours,
)

from heshly_core.services.calendar.calendar_manager import (
    CalendarManager,
)

from heshly_core.models.calendar_provider import (
    ProviderConnection,
)

from heshly_core.services.calendar.providers.provider_integration import (
    ProviderIntegration,
)


class CalendarIntegration:
    """
    Public integration point for the
    Calendar & Scheduling module.

    Other modules should communicate
    with the calendar subsystem through
    this class.
    """

    def __init__(
        self,
        provider: ProviderIntegration | None = None,
    ) -> None:

        self._manager = CalendarManager(
            provider=provider,
        )

    @property
    def manager(
        self,
    ) -> CalendarManager:

        return self._manager

    def check_availability(
        self,
        request: AvailabilityRequest,
        events,
        working_start,
        working_end,
    ):

        return self._manager.check_availability(

            request=request,

            events=events,

            working_start=working_start,

            working_end=working_end,
        )

    def connect(
        self,
        connection: ProviderConnection,
    ) -> bool:
        return self._manager.provider.connect(
            connection
        )

    def book(
        self,
        request: AppointmentRequest,
        events,
    ):

        return self._manager.book(

            request,

            events,
        )

    def cancel(
        self,
        appointment_id: str,
    ):

        return self._manager.cancel(

            appointment_id,
        )

    def reschedule(
        self,
        request: AppointmentRequest,
        events,
    ):

        return self._manager.reschedule(

            request,

            events,
        )

    def validate_business_hours(
        self,
        request: AppointmentRequest,
        hours: BusinessHours,
    ):

        return self._manager.validate_business_hours(

            request,

            hours,
        )

    def detect_conflicts(
        self,
        request: AppointmentRequest,
        events,
    ):

        return self._manager.detect_conflicts(

            request,

            events,
        )