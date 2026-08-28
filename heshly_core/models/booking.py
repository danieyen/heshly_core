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
    Tolerant to n8n capitalized Business/Entities and separate date/time.
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
        # Unwrap n8n wrappers
        if "data" in data and isinstance(data["data"], dict) and any(k in data["data"] for k in ("Business", "Entities", "business", "entities", "service")):
            data = data["data"]
        if "body" in data and isinstance(data["body"], dict) and any(k in data["body"] for k in ("Business", "Entities", "service")):
            data = data["body"]
        # Handle capitalized Entities/Business
        entities = None
        for ekey in ("Entities", "entities"):
            if ekey in data and isinstance(data[ekey], dict):
                entities = data[ekey]
                break
        # Resolve service
        service = data.get("service") or data.get("Service")
        if not service and entities:
            service = entities.get("service") or entities.get("Service") or entities.get("service_name")
        # Resolve preferred_date
        preferred_date = data.get("preferred_date") or data.get("date") or data.get("Date")
        if not preferred_date and entities:
            preferred_date = entities.get("preferred_date") or entities.get("date") or entities.get("Date")
            # handle scheduled_time inside entities
            if not preferred_date and entities.get("scheduled_time"):
                try:
                    from datetime import datetime
                    st = str(entities["scheduled_time"])
                    if "T" in st:
                        preferred_date = st.split("T")[0]
                    else:
                        preferred_date = st
                except Exception:
                    pass
        # Resolve preferred_time
        preferred_time = data.get("preferred_time") or data.get("time") or data.get("Time")
        if not preferred_time and entities:
            preferred_time = entities.get("preferred_time") or entities.get("time") or entities.get("Time")
            if not preferred_time and entities.get("scheduled_time"):
                try:
                    st = str(entities["scheduled_time"])
                    if "T" in st:
                        tpart = st.split("T")[1].split(".")[0].split("Z")[0].split("+")[0]
                        preferred_time = tpart[:5] if len(tpart) >= 5 else tpart
                except Exception:
                    pass
        # Handle n8n sending start as ISO
        if not preferred_date and data.get("start"):
            try:
                from datetime import datetime
                start = datetime.fromisoformat(str(data["start"]).replace("Z", "+00:00"))
                preferred_date = start.date().isoformat()
                preferred_time = start.time().strftime("%H:%M")
            except Exception:
                pass
        if not preferred_date and data.get("scheduled_time"):
            try:
                from datetime import datetime
                st = str(data["scheduled_time"])
                if "T" in st:
                    start = datetime.fromisoformat(st.replace("Z", "+00:00"))
                    preferred_date = start.date().isoformat()
                    if not preferred_time:
                        preferred_time = start.time().strftime("%H:%M")
                else:
                    preferred_date = st.split("T")[0]
            except Exception:
                pass
        # Also handle separate preferred_date/preferred_time at top level that may be date object
        if preferred_date:
            preferred_date = str(preferred_date).split("T")[0].strip()
        if preferred_time:
            pt = str(preferred_time).strip()
            # normalize HH:MM:SS to HH:MM
            if len(pt.split(":")) == 3:
                pt = ":".join(pt.split(":")[:2])
            preferred_time = pt
        duration = data.get("duration_minutes") or data.get("duration") or data.get("Duration")
        if duration is None and entities:
            duration = entities.get("duration_minutes") or entities.get("duration")
        if duration is not None:
            try:
                duration = int(duration)
            except Exception:
                duration = None
        # customer_id may be under Customer
        customer_id = data.get("customer_id") or data.get("customerId") or data.get("customer_id")
        if not customer_id:
            for ckey in ("Customer", "customer"):
                if ckey in data and isinstance(data[ckey], dict):
                    c = data[ckey]
                    customer_id = c.get("id") or c.get("customer_id") or c.get("customerId")
                    if customer_id:
                        break
        if not customer_id:
            for lkey in ("Lead", "lead"):
                if lkey in data and isinstance(data[lkey], dict):
                    l = data[lkey]
                    customer_id = l.get("id") or l.get("lead_id")
                    if customer_id:
                        break
        # preferred_staff
        preferred_staff = data.get("preferred_staff") or data.get("staff") or data.get("Staff")
        if not preferred_staff and entities:
            preferred_staff = entities.get("preferred_staff") or entities.get("staff")
        return cls(
            customer_id=str(customer_id or ""),
            service=str(service).strip() if service else None,
            preferred_staff=str(preferred_staff).strip() if preferred_staff else None,
            preferred_date=str(preferred_date).strip() if preferred_date else None,
            preferred_time=str(preferred_time).strip() if preferred_time else None,
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
