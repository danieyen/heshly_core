from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConversationOutcome(str, Enum):
    """
    Final outcome of a conversation.
    """

    BOOKED = "booked"

    QUALIFIED = "qualified"

    HANDOVER = "handover"

    COMPLETED = "completed"

    CANCELLED = "cancelled"

    ABANDONED = "abandoned"

    FAILED = "failed"


class FeedbackRating(int, Enum):
    """
    Customer satisfaction rating.
    """

    VERY_POOR = 1

    POOR = 2

    AVERAGE = 3

    GOOD = 4

    EXCELLENT = 5


class LearningEventType(str, Enum):
    """
    Types of learning events.
    """

    OUTCOME = "outcome"

    FEEDBACK = "feedback"

    DECISION = "decision"

    ERROR = "error"

    HUMAN_CORRECTION = "human_correction"

    METRIC = "metric"


class FailureType(str, Enum):
    """
    Categories of operational failures.
    """

    VALIDATION = "validation"

    BOOKING = "booking"

    INTEGRATION = "integration"

    AI = "ai"

    DATABASE = "database"

    TIMEOUT = "timeout"

    UNKNOWN = "unknown"


@dataclass(slots=True)
class ConversationOutcomeRecord:
    """
    Stores the final result of a conversation.
    """

    conversation_id: str

    customer_id: str

    outcome: ConversationOutcome

    completed_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class CustomerFeedback:
    """
    Stores customer satisfaction feedback.
    """

    conversation_id: str

    customer_id: str

    rating: FeedbackRating

    comment: str | None = None

    would_recommend: bool | None = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class AIDecisionRecord:
    """
    Records a decision made by an AI engine.
    """

    conversation_id: str

    customer_id: str

    engine: str

    decision: str

    confidence: float

    reasoning: str

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class FailureRecord:
    """
    Records system or AI failures.
    """

    conversation_id: str

    customer_id: str

    failure_type: FailureType

    source: str

    message: str

    recoverable: bool = True

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class HumanCorrectionRecord:
    """
    Records human overrides of AI decisions.
    """

    conversation_id: str

    customer_id: str

    engine: str

    original_decision: str

    corrected_decision: str

    reason: str

    corrected_by: str

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class PerformanceMetrics:
    """
    Aggregated AI performance measurements.
    """

    total_conversations: int = 0

    booked_conversations: int = 0

    qualified_conversations: int = 0

    handovers: int = 0

    failures: int = 0

    human_corrections: int = 0

    average_feedback_score: float = 0.0

    booking_rate: float = 0.0

    qualification_rate: float = 0.0

    escalation_rate: float = 0.0

    correction_rate: float = 0.0

    generated_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class LearningEvent:
    """
    Generic learning event record.
    """

    event_type: LearningEventType

    conversation_id: str

    customer_id: str

    description: str

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

@dataclass(slots=True)
class Recommendation:
    """
    Improvement suggestion generated from learning data.
    """

    category: str

    title: str

    description: str

    priority: str

    confidence: float

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )