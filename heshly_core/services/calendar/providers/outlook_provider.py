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


class OutlookCalendarProvider(
    CalendarProviderInterface,
):
    """
    Microsoft Outlook Calendar provider.

    Future implementation will interact
    with Microsoft Graph Calendar APIs.
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

            provider="Microsoft Outlook",

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
        # Retrieve calendar events
        # from Microsoft Graph.
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
        # Create Outlook event.
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
        # Update Outlook event.
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
        # Delete Outlook event.
        #

        return ProviderAppointmentResult(

            success=True,

            event_id=event_id,

            message="Appointment deleted.",

        )