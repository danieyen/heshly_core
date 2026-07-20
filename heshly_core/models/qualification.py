from dataclasses import dataclass, field
from enum import Enum


class QualificationStatus(str, Enum):
    """
    Current qualification state.
    """

    UNKNOWN = "unknown"
    COLLECTING_INFO = "collecting_info"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    ESCALATED = "escalated"


class QualificationAction(str, Enum):
    """
    Next conversational action after qualification.
    """

    ASK_QUESTION = "ask_question"
    PROCEED_TO_BOOKING = "proceed_to_booking"
    ESCALATE = "escalate"
    END_CONVERSATION = "end_conversation"


class UrgencyLevel(str, Enum):
    """
    Customer urgency classification.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass(slots=True)
class QualificationResult:
    """
    Result produced by the Qualification Engine.
    """

    customer_id: str

    status: QualificationStatus = (
        QualificationStatus.UNKNOWN
    )

    urgency: UrgencyLevel = (
        UrgencyLevel.LOW
    )

    score: float = 0.0

    eligible: bool = True

    eligibility_reason: str | None = None

    missing_fields: list[str] = field(
        default_factory=list
    )

    reasons: list[str] = field(
        default_factory=list
    )