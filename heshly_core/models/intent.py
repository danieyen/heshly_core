from dataclasses import dataclass
from enum import Enum


class Intent(Enum):
    BOOK_APPOINTMENT = "book_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    SERVICE_INQUIRY = "service_inquiry"
    PRICE_INQUIRY = "price_inquiry"
    BUSINESS_HOURS = "business_hours"
    LOCATION = "location"
    GREETING = "greeting"
    HUMAN_SUPPORT = "human_support"
    UNKNOWN = "unknown"

    @property
    def is_booking_intent(self) -> bool:
        return self in (Intent.BOOK_APPOINTMENT, Intent.RESCHEDULE_APPOINTMENT)

    @property
    def requires_human(self) -> bool:
        return self == Intent.HUMAN_SUPPORT


@dataclass(slots=True)
class IntentResult:
    intent: Intent
    confidence: float
    reasoning: str

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.7

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value if isinstance(self.intent, Enum) else str(self.intent),
            "confidence": float(self.confidence),
            "reasoning": self.reasoning,
        }
