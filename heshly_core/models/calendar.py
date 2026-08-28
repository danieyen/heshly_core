from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, UTC
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

    @property
    def is_blocking(self) -> bool:
        return self not in (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)


@dataclass(slots=True)
class TimeSlot:
    """
    A single available time slot.
    """

    start: datetime

    end: datetime

    available: bool = True

    def to_dict(self) -> dict:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "available": self.available,
        }


@dataclass(slots=True)
class BusinessHours:
    """
    Business operating hours.
    """

    weekday: int

    opens_at: time

    closes_at: time

    enabled: bool = True

    def is_valid(self) -> bool:
        return self.opens_at < self.closes_at


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

    def is_blocking(self) -> bool:
        return self.status.is_blocking


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

    preferred_staff: str | None = None

    def validate(self) -> list[str]:
        errors = []
        if not self.service:
            errors.append("service is required")
        if not self.preferred_date:
            errors.append("preferred_date is required")
        if self.duration_minutes <= 0:
            errors.append("duration_minutes must be > 0")
        return errors


@dataclass(slots=True)
class AvailabilityResult:
    """
    Available appointment slots.
    Contract used by n8n: { available: bool, slots: [...] }
    Must return object, not JSON string.
    """

    available: bool

    slots: list[TimeSlot] = field(
        default_factory=list
    )

    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "available": bool(self.available),
            "slots": [s.to_dict() for s in self.slots],
            "reason": self.reason,
        }


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

    def validate(self) -> list[str]:
        errors = []
        if not self.customer_name:
            errors.append("customer_name is required")
        if not self.customer_phone:
            errors.append("customer_phone is required")
        if not self.service:
            errors.append("service is required")
        if not self.start:
            errors.append("start is required")
        if self.duration_minutes <= 0:
            errors.append("duration_minutes must be > 0")
        return errors


@dataclass(slots=True)
class AppointmentResult:
    """
    Appointment operation result.
    Contract used by n8n booking response: { success: bool, appointment_id, status, message }
    success must be boolean, not string.
    """

    success: bool

    appointment_id: str | None = None

    status: AppointmentStatus | None = None

    message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": bool(self.success),
            "appointment_id": self.appointment_id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "message": self.message,
        }
