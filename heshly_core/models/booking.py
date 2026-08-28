from dataclasses import dataclass, field
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


class BookingStatus(str, Enum):
    """
    Current booking state.
    """

    PENDING = "pending"
    SEARCHING = "searching"
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (BookingStatus.CONFIRMED, BookingStatus.FAILED, BookingStatus.CANCELLED)

    @classmethod
    def from_value(cls, value: Any) -> "BookingStatus":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls(value.strip().lower())
            except ValueError:
                return cls.PENDING
        return cls.PENDING


class BookingAction(str, Enum):
    """
    Next conversational action for the Booking Engine.
    Maps to n8n Switch routing and workflow Action.
    """

    ASK_INFORMATION = "ask_information"
    PRESENT_OPTIONS = "present_options"
    CONFIRM_BOOKING = "confirm_booking"
    END_CONVERSATION = "end_conversation"


@dataclass(slots=True)
class BookingRequest:
    """
    Customer booking request.
    """

    customer_id: str

    service: str | None = None

    preferred_staff: str | None = None

    preferred_date: str | None = None

    preferred_time: str | None = None

    duration_minutes: int | None = None

    def is_complete(self) -> bool:
        return bool(self.service and self.preferred_date and self.preferred_time)

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.service:
            missing.append("service")
        if not self.preferred_date:
            missing.append("preferred_date")
        if not self.preferred_time:
            missing.append("preferred_time")
        return missing

    @classmethod
    def from_dict(cls, data: Any) -> "BookingRequest":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("BookingRequest data must be dict")
        # Handle n8n sending start as ISO
        preferred_date = data.get("preferred_date") or data.get("date")
        preferred_time = data.get("preferred_time") or data.get("time")
        if not preferred_date and data.get("start"):
            try:
                from datetime import datetime
                start = datetime.fromisoformat(str(data["start"]).replace("Z", "+00:00"))
                preferred_date = start.date().isoformat()
                preferred_time = start.time().strftime("%H:%M")
            except Exception:
                pass
        duration = data.get("duration_minutes") or data.get("duration")
        if duration is not None:
            try:
                duration = int(duration)
            except Exception:
                duration = None
        return cls(
            customer_id=str(data.get("customer_id") or data.get("customerId") or ""),
            service=data.get("service"),
            preferred_staff=data.get("preferred_staff") or data.get("staff"),
            preferred_date=str(preferred_date) if preferred_date else None,
            preferred_time=str(preferred_time) if preferred_time else None,
            duration_minutes=duration,
        )

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "service": self.service,
            "preferred_staff": self.preferred_staff,
            "preferred_date": self.preferred_date,
            "preferred_time": self.preferred_time,
            "duration_minutes": self.duration_minutes,
        }


@dataclass(slots=True)
class BookingOption:
    """
    One available booking option.
    """

    service: str

    staff: str

    date: str

    time: str

    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "staff": self.staff,
            "date": self.date,
            "time": self.time,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "BookingOption":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("BookingOption data must be dict")
        return cls(
            service=str(data.get("service") or ""),
            staff=str(data.get("staff") or ""),
            date=str(data.get("date") or ""),
            time=str(data.get("time") or ""),
            score=float(data.get("score") or 0.0),
        )


@dataclass(slots=True)
class BookingResult:
    """
    Result produced by the Booking Engine.
    Contract must match n8n availability response structure:
    { status, selected_option, options, reason }
    """

    request: BookingRequest

    status: BookingStatus = BookingStatus.PENDING

    selected_option: BookingOption | None = None

    options: list[BookingOption] = field(
        default_factory=list
    )

    reason: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == BookingStatus.CONFIRMED

    @property
    def has_options(self) -> bool:
        return len(self.options) > 0

    def to_dict(self) -> dict:
        return {
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "selected_option": self.selected_option.to_dict() if self.selected_option else None,
            "options": [o.to_dict() for o in self.options],
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "BookingResult":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("BookingResult data must be dict")
        request_data = data.get("request") or {}
        request = BookingRequest.from_dict(request_data) if isinstance(request_data, dict) else BookingRequest(customer_id="")
        status = BookingStatus.from_value(data.get("status"))
        selected = None
        if data.get("selected_option") and isinstance(data["selected_option"], dict):
            try:
                selected = BookingOption.from_dict(data["selected_option"])
            except Exception:
                selected = None
        options = []
        for o in data.get("options", []) or []:
            if isinstance(o, dict):
                try:
                    options.append(BookingOption.from_dict(o))
                except Exception:
                    continue
        return cls(
            request=request,
            status=status,
            selected_option=selected,
            options=options,
            reason=data.get("reason"),
        )
