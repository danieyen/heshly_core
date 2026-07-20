from __future__ import annotations

from heshly_core.models.calendar import (
    CalendarEvent,
)

from heshly_core.models.calendar_provider import (
    ProviderAppointmentResult,
    ProviderConnection,
    ProviderEventQuery,
    ProviderEventsResult,
    ProviderHealth,
)

from heshly_core.services.calendar.providers.provider_manager import (
    ProviderManager,
)


class ProviderIntegration:
    """
    High-level integration for the
    calendar provider subsystem.

    This is the entry point used by the
    scheduling module when interacting
    with calendar providers.
    """

    def __init__(
        self,
    ) -> None:

        self._manager = (
            ProviderManager()
        )

    def connect(
        self,
        connection: ProviderConnection,
    ) -> bool:

        return self._manager.connect(
            connection
        )

    def disconnect(
        self,
    ) -> None:

        self._manager.disconnect()

    def health(
        self,
    ) -> ProviderHealth:

        return self._manager.health()

    def get_events(
        self,
        query: ProviderEventQuery,
    ) -> ProviderEventsResult:

        return self._manager.get_events(
            query
        )

    def create_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        return self._manager.create_event(
            event
        )

    def update_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        return self._manager.update_event(
            event
        )

    def delete_event(
        self,
        event_id: str,
    ) -> ProviderAppointmentResult:

        return self._manager.delete_event(
            event_id
        )

    @property
    def manager(
        self,
    ) -> ProviderManager:

        return self._manager