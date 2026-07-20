from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum


class CalendarProvider(str, Enum):
    """
    Supported calendar providers.
    """

    ERPNEXT = "erpnext"

    GOOGLE = "google"

    OUTLOOK = "outlook"

    ICAL = "ical"

    CUSTOM = "custom"


class AppointmentStatus(str, Enum):
    """
    Appointment lifecycle.
    """

    PENDING = "pending"

    CONFIRMED = "confirmed"

    CANCELLED = "cancelled"

    COMPLETED = "completed"

    NO_SHOW = "no_show"

    RESCHEDULED = "rescheduled"


@dataclass(slots=True)
class TimeSlot:
    """
    A single available time slot.
    """

    start: datetime

    end: datetime

    available: bool = True


@dataclass(slots=True)
class BusinessHours:
    """
    Business operating hours.
    """

    weekday: int

    opens_at: time

    closes_at: time

    enabled: bool = True


@dataclass(slots=True)
class CalendarEvent:
    """
    Calendar event.
    """

    event_id: str

    title: str

    start: datetime

    end: datetime

    customer_name: str | None = None

    customer_phone: str | None = None

    notes: str | None = None

    status: AppointmentStatus = (
        AppointmentStatus.CONFIRMED
    )


@dataclass(slots=True)
class CalendarConfiguration:
    """
    Calendar provider configuration.
    """

    provider: CalendarProvider

    calendar_id: str

    timezone: str

    business_name: str

    settings: dict = field(
        default_factory=dict
    )


@dataclass(slots=True)
class AvailabilityRequest:
    """
    Request for available slots.
    """

    service: str

    preferred_date: date

    duration_minutes: int


@dataclass(slots=True)
class AvailabilityResult:
    """
    Available appointment slots.
    """

    available: bool

    slots: list[TimeSlot] = field(
        default_factory=list
    )


@dataclass(slots=True)
class AppointmentRequest:
    """
    Request to create
    an appointment.
    """

    customer_name: str

    customer_phone: str

    service: str

    start: datetime

    duration_minutes: int

    notes: str | None = None


@dataclass(slots=True)
class AppointmentResult:
    """
    Appointment operation result.
    """

    success: bool

    appointment_id: str | None = None

    status: AppointmentStatus | None = None

    message: str = ""