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


@dataclass(slots=True)
class IntentResult:
    intent: Intent
    confidence: float
    reasoning: str