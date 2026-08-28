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
    Tolerant to n8n capitalized Business/Entities and date/time variations.
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
        # Unwrap n8n wrappers
        if "data" in data and isinstance(data["data"], dict) and any(k in data["data"] for k in ("Business", "Entities", "business", "entities", "service")):
            data = data["data"]
        if "body" in data and isinstance(data["body"], dict) and any(k in data["body"] for k in ("Business", "Entities", "service")):
            data = data["body"]
        entities = None
        for ekey in ("Entities", "entities"):
            if ekey in data and isinstance(data[ekey], dict):
                entities = data[ekey]
                break
        # service
        service = data.get("service") or data.get("service_name") or data.get("Service")
        if not service and entities:
            service = entities.get("service") or entities.get("Service") or entities.get("service_name")
        # preferred_date
        pref_date = data.get("preferred_date") or data.get("date") or data.get("Date")
        if not pref_date and entities:
            pref_date = entities.get("preferred_date") or entities.get("date") or entities.get("Date") or entities.get("scheduled_time")
        if isinstance(pref_date, str):
            try:
                # handle ISO datetime
                if "T" in pref_date:
                    pref_date = pref_date.split("T")[0]
                pref_date = date.fromisoformat(pref_date.split("T")[0])
            except Exception:
                pref_date = None
        elif isinstance(pref_date, datetime):
            pref_date = pref_date.date()
        # Handle n8n sending start as ISO datetime
        if not pref_date and data.get("start"):
            try:
                start = datetime.fromisoformat(str(data["start"]).replace("Z", "+00:00"))
                pref_date = start.date()
            except Exception:
                pass
        if not pref_date and data.get("scheduled_time"):
            try:
                st = str(data["scheduled_time"])
                if "T" in st:
                    pref_date = date.fromisoformat(st.split("T")[0])
                else:
                    pref_date = date.fromisoformat(st.split("T")[0])
            except Exception:
                pass
        duration = data.get("duration_minutes") or data.get("duration") or data.get("Duration") or 30
        if duration is None and entities:
            duration = entities.get("duration_minutes") or entities.get("duration") or 30
        try:
            duration = int(duration)
        except Exception:
            duration = 30
        preferred_staff = data.get("preferred_staff") or data.get("staff") or data.get("Staff")
        if not preferred_staff and entities:
            preferred_staff = entities.get("preferred_staff") or entities.get("staff")
        return cls(
            service=str(service or ""),
            preferred_date=pref_date,
            duration_minutes=duration,
            preferred_staff=str(preferred_staff).strip() if preferred_staff else None,
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
        # handle wrapped message
        if "message" in data and isinstance(data["message"], dict) and "available" in data["message"]:
            data = data["message"]
        slots = []
        for s in data.get("slots", []) or []:
            if isinstance(s, dict):
                try:
                    slots.append(TimeSlot.from_dict(s))
                except Exception:
                    continue
            elif isinstance(s, str):
                # handle stringified slot
                try:
                    import json
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        slots.append(TimeSlot.from_dict(obj))
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
    Tolerant to n8n capitalized Business/Entities/Customer and scheduled_time variations.
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
        # Unwrap n8n wrappers
        if "data" in data and isinstance(data["data"], dict) and any(k in data["data"] for k in ("Business", "Entities", "Customer", "business", "entities", "service")):
            data = data["data"]
        if "body" in data and isinstance(data["body"], dict) and any(k in data["body"] for k in ("Business", "Entities", "service")):
            data = data["body"]
        entities = None
        for ekey in ("Entities", "entities"):
            if ekey in data and isinstance(data[ekey], dict):
                entities = data[ekey]
                break
        # Handle n8n sending separate date+time
        start = data.get("start") or data.get("scheduled_time") or data.get("scheduledTime") or data.get("appointment_date")
        if not start and entities:
            start = entities.get("scheduled_time") or entities.get("start") or entities.get("date")
        if not start and data.get("preferred_date") and data.get("preferred_time"):
            try:
                date_str = str(data["preferred_date"]).split("T")[0]
                time_str = str(data["preferred_time"])
                if len(time_str.split(":")) == 2:
                    time_str = time_str + ":00"
                start = datetime.fromisoformat(f"{date_str}T{time_str}:00")
            except Exception:
                start = None
        if not start and entities:
            pd = entities.get("preferred_date") or entities.get("date")
            pt = entities.get("preferred_time") or entities.get("time")
            if pd and pt:
                try:
                    date_str = str(pd).split("T")[0]
                    time_str = str(pt)
                    if len(time_str.split(":")) == 2:
                        time_str = time_str + ":00"
                    start = datetime.fromisoformat(f"{date_str}T{time_str}:00")
                except Exception:
                    start = None
            elif pd and not pt:
                try:
                    date_str = str(pd).split("T")[0]
                    start = datetime.fromisoformat(f"{date_str}T00:00:00")
                except Exception:
                    start = None
        if isinstance(start, str):
            try:
                # handle date only
                if "T" not in start and len(start.split("-")) == 3:
                    start = start + "T00:00:00"
                start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except Exception:
                start = None
        duration = data.get("duration_minutes") or data.get("duration") or data.get("Duration") or 30
        if duration is None and entities:
            duration = entities.get("duration_minutes") or entities.get("duration") or 30
        try:
            duration = int(duration)
        except Exception:
            duration = 30
        # customer_name/phone may be under Customer
        customer_name = data.get("customer_name") or data.get("customerName") or data.get("name") or data.get("full_name")
        customer_phone = data.get("customer_phone") or data.get("customerPhone") or data.get("phone")
        if not customer_name or not customer_phone:
            for ckey in ("Customer", "customer"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    if not customer_name:
                        customer_name = c.get("name") or c.get("full_name") or c.get("customer_name")
                    if not customer_phone:
                        customer_phone = c.get("phone") or c.get("customer_phone") or c.get("mobile_no")
        if not customer_name and entities:
            customer_name = entities.get("name") or entities.get("full_name")
        if not customer_phone and entities:
            customer_phone = entities.get("phone")
        # service
        service = data.get("service") or data.get("Service")
        if not service and entities:
            service = entities.get("service") or entities.get("Service")
        return cls(
            customer_name=str(customer_name or "").strip(),
            customer_phone=str(customer_phone or "").strip(),
            service=str(service or "").strip(),
            start=start,
            duration_minutes=duration,
            notes=data.get("notes") or (entities.get("notes") if entities else None),
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
        if "message" in data and isinstance(data["message"], dict) and "success" in data["message"]:
            data = data["message"]
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
