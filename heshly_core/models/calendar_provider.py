from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from heshly_core.models.calendar import (
    CalendarConfiguration,
    CalendarEvent,
)


class CalendarProviderStatus(str, Enum):
    """
    Calendar provider status.
    """

    AVAILABLE = "available"

    UNAVAILABLE = "unavailable"

    ERROR = "error"


@dataclass(slots=True)
class ProviderConnection:
    """
    Connection details for a calendar provider.
    """

    configuration: CalendarConfiguration

    access_token: str | None = None

    refresh_token: str | None = None

    expires_at: datetime | None = None


@dataclass(slots=True)
class ProviderEventQuery:
    """
    Request for calendar events.
    """

    start: datetime

    end: datetime


@dataclass(slots=True)
class ProviderEventsResult:
    """
    Events returned by a provider.
    """

    success: bool

    events: list[CalendarEvent] = field(
        default_factory=list
    )

    message: str = ""


@dataclass(slots=True)
class ProviderAppointmentResult:
    """
    Result of creating, updating,
    or deleting an appointment.
    """

    success: bool

    event_id: str | None = None

    message: str = ""


@dataclass(slots=True)
class ProviderHealth:
    """
    Provider health information.
    """

    status: CalendarProviderStatus

    provider: str

    message: str = ""