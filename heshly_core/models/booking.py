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


class BookingAction(str, Enum):
    """
    Next conversational action for the Booking Engine.
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


@dataclass(slots=True)
class BookingResult:
    """
    Result produced by the Booking Engine.
    """

    request: BookingRequest

    status: BookingStatus = BookingStatus.PENDING

    selected_option: BookingOption | None = None

    options: list[BookingOption] = field(
        default_factory=list
    )

    reason: str | None = None