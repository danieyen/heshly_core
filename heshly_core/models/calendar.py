from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, UTC
from enum import Enum
from typing import Any


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y")
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]")):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


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
            "available": bool(self.available),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeSlot":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("TimeSlot data must be dict")
        start = data.get("start")
        end = data.get("end")
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return cls(
            start=start,
            end=end,
            available=_normalize_bool(data.get("available", True)),
        )


@dataclass(slots=True)
class BusinessHours:
    """
    Business operating hours.
    Canonical definition - all code must import from here.
    """

    weekday: int

    opens_at: time

    closes_at: time

    enabled: bool = True

    def is_valid(self) -> bool:
        return self.opens_at < self.closes_at

    @property
    def opening_time(self) -> time:
        return self.opens_at

    @property
    def closing_time(self) -> time:
        return self.closes_at


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

    @classmethod
    def from_dict(cls, data: dict) -> "AvailabilityRequest":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("AvailabilityRequest data must be dict")
        # Handle n8n sending date as string
        pref_date = data.get("preferred_date") or data.get("date")
        if isinstance(pref_date, str):
            try:
                pref_date = date.fromisoformat(pref_date.split("T")[0])
            except Exception:
                pref_date = None
        # Handle n8n sending start as ISO datetime
        if not pref_date and data.get("start"):
            try:
                start = datetime.fromisoformat(str(data["start"]).replace("Z", "+00:00"))
                pref_date = start.date()
            except Exception:
                pass
        duration = data.get("duration_minutes") or data.get("duration") or 30
        try:
            duration = int(duration)
        except Exception:
            duration = 30
        return cls(
            service=str(data.get("service") or data.get("service_name") or ""),
            preferred_date=pref_date,
            duration_minutes=duration,
            preferred_staff=data.get("preferred_staff") or data.get("staff"),
        )


@dataclass(slots=True)
class AvailabilityResult:
    """
    Available appointment slots.
    Contract used by n8n: { available: bool, slots: [...] }
    Must return object, not JSON string. available MUST be boolean.
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

    @classmethod
    def from_dict(cls, data: Any) -> "AvailabilityResult":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("AvailabilityResult data must be dict")
        slots = []
        for s in data.get("slots", []) or []:
            if isinstance(s, dict):
                try:
                    slots.append(TimeSlot.from_dict(s))
                except Exception:
                    continue
        return cls(
            available=_normalize_bool(data.get("available", False)),
            slots=slots,
            reason=str(data.get("reason") or ""),
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

    @classmethod
    def from_dict(cls, data: dict) -> "AppointmentRequest":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("AppointmentRequest data must be dict")
        # Handle n8n sending separate date+time
        start = data.get("start")
        if not start and data.get("preferred_date") and data.get("preferred_time"):
            try:
                date_str = str(data["preferred_date"]).split("T")[0]
                time_str = str(data["preferred_time"])
                start = datetime.fromisoformat(f"{date_str}T{time_str}:00")
            except Exception:
                start = None
        if isinstance(start, str):
            try:
                start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except Exception:
                start = None
        duration = data.get("duration_minutes") or data.get("duration") or 30
        try:
            duration = int(duration)
        except Exception:
            duration = 30
        return cls(
            customer_name=str(data.get("customer_name") or data.get("customerName") or data.get("name") or ""),
            customer_phone=str(data.get("customer_phone") or data.get("customerPhone") or data.get("phone") or ""),
            service=str(data.get("service") or ""),
            start=start,
            duration_minutes=duration,
            notes=data.get("notes"),
        )


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

    @classmethod
    def from_dict(cls, data: Any) -> "AppointmentResult":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("AppointmentResult data must be dict")
        status = data.get("status")
        if isinstance(status, str) and status:
            try:
                status = AppointmentStatus(status)
            except ValueError:
                status = None
        return cls(
            success=_normalize_bool(data.get("success", False)),
            appointment_id=data.get("appointment_id") or data.get("appointmentId"),
            status=status,
            message=str(data.get("message") or ""),
        )
