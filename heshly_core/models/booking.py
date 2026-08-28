from dataclasses import dataclass, field
from enum import Enum


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
