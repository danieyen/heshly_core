from __future__ import annotations

from heshly_core.models.calendar import (
    CalendarEvent,
)

from heshly_core.models.calendar_provider import (
    CalendarProviderStatus,
    ProviderAppointmentResult,
    ProviderConnection,
    ProviderEventQuery,
    ProviderEventsResult,
    ProviderHealth,
)

from heshly_core.services.calendar.providers.provider_interface import (
    CalendarProviderInterface,
)


class ERPNextCalendarProvider(
    CalendarProviderInterface,
):
    """
    ERPNext calendar provider.

    Future implementation will interact
    with ERPNext Appointment DocTypes.
    """

    def __init__(
        self,
    ) -> None:

        self._connection: (
            ProviderConnection | None
        ) = None

    def connect(
        self,
        connection: ProviderConnection,
    ) -> bool:

        self._connection = connection

        return True

    def disconnect(
        self,
    ) -> None:

        self._connection = None

    def health(
        self,
    ) -> ProviderHealth:

        status = (
            CalendarProviderStatus.AVAILABLE
            if self._connection
            else CalendarProviderStatus.UNAVAILABLE
        )

        return ProviderHealth(

            status=status,

            provider="ERPNext",

            message=(
                "Connected"
                if self._connection
                else "Not connected"
            ),
        )

    def get_events(
        self,
        query: ProviderEventQuery,
    ) -> ProviderEventsResult:

        #
        # Future:
        # Read Appointment records
        # from ERPNext.
        #

        return ProviderEventsResult(

            success=True,

            events=[],

            message="No events.",
        )

    def create_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        #
        # Future:
        # Create ERPNext Appointment.
        #

        return ProviderAppointmentResult(

            success=True,

            event_id=event.event_id,

            message="Appointment created.",
        )

    def update_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        #
        # Future:
        # Update ERPNext Appointment.
        #

        return ProviderAppointmentResult(

            success=True,

            event_id=event.event_id,

            message="Appointment updated.",
        )

    def delete_event(
        self,
        event_id: str,
    ) -> ProviderAppointmentResult:

        #
        # Future:
        # Delete ERPNext Appointment.
        #

        return ProviderAppointmentResult(

            success=True,

            event_id=event_id,

            message="Appointment deleted.",
        )