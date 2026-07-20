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

from heshly_core.services.calendar.providers.provider_factory import (
    ProviderFactory,
)

from heshly_core.services.calendar.providers.provider_interface import (
    CalendarProviderInterface,
)


class ProviderManager:
    """
    Coordinates calendar providers.

    This class is the primary entry point
    for interacting with calendar providers.
    """

    def __init__(
        self,
        factory: ProviderFactory | None = None,
    ) -> None:

        self._factory = (
            factory
            or ProviderFactory()
        )

        self._provider: (
            CalendarProviderInterface | None
        ) = None

    def connect(
        self,
        connection: ProviderConnection,
    ) -> bool:

        self._provider = self._factory.create(
            connection.configuration.provider
        )

        return self._provider.connect(
            connection
        )

    def disconnect(
        self,
    ) -> None:

        if self._provider:

            self._provider.disconnect()

            self._provider = None

    def health(
        self,
    ) -> ProviderHealth:

        self._ensure_connected()

        return self._provider.health()

    def get_events(
        self,
        query: ProviderEventQuery,
    ) -> ProviderEventsResult:

        self._ensure_connected()

        return self._provider.get_events(
            query
        )

    def create_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        self._ensure_connected()

        return self._provider.create_event(
            event
        )

    def update_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        self._ensure_connected()

        return self._provider.update_event(
            event
        )

    def delete_event(
        self,
        event_id: str,
    ) -> ProviderAppointmentResult:

        self._ensure_connected()

        return self._provider.delete_event(
            event_id
        )

    def _ensure_connected(
        self,
    ) -> None:

        if self._provider is None:

            raise RuntimeError(
                "No calendar provider is connected."
            )