from __future__ import annotations

from abc import ABC
from abc import abstractmethod

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


class CalendarProviderInterface(
    ABC,
):
    """
    Base interface implemented by every
    calendar provider.
    """

    @abstractmethod
    def connect(
        self,
        connection: ProviderConnection,
    ) -> bool:
        """
        Establish a connection with the
        calendar provider.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(
        self,
    ) -> None:
        """
        Close the provider connection.
        """
        raise NotImplementedError

    @abstractmethod
    def health(
        self,
    ) -> ProviderHealth:
        """
        Return provider health.
        """
        raise NotImplementedError

    @abstractmethod
    def get_events(
        self,
        query: ProviderEventQuery,
    ) -> ProviderEventsResult:
        """
        Retrieve events within a time range.
        """
        raise NotImplementedError

    @abstractmethod
    def create_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:
        """
        Create a calendar event.
        """
        raise NotImplementedError

    @abstractmethod
    def update_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:
        """
        Update a calendar event.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_event(
        self,
        event_id: str,
    ) -> ProviderAppointmentResult:
        """
        Delete a calendar event.
        """
        raise NotImplementedError