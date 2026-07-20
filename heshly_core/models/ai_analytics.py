from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# ==========================================================
# Analytics Period
# ==========================================================

class AIAnalyticsPeriod(str, Enum):

    DAILY = "daily"

    WEEKLY = "weekly"

    MONTHLY = "monthly"

    QUARTERLY = "quarterly"

    YEARLY = "yearly"

    CUSTOM = "custom"


# ==========================================================
# AI Session
# ==========================================================

@dataclass(slots=True)
class AISessionAnalytics:

    session_id: str

    customer_id: str | None = None

    started_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    ended_at: datetime | None = None

    duration_seconds: int = 0

    messages: int = 0

    user_messages: int = 0

    ai_messages: int = 0

    intents_detected: int = 0

    entities_extracted: int = 0

    confidence_score: float = 0.0

    resolved: bool = False

    handed_to_human: bool = False

    booking_created: bool = False

    sentiment: str = "neutral"

    metadata: dict = field(
        default_factory=dict
    )


# ==========================================================
# Intent Analytics
# ==========================================================

@dataclass(slots=True)
class IntentAnalytics:

    intent: str

    count: int = 0

    average_confidence: float = 0.0

    success_rate: float = 0.0


# ==========================================================
# AI Performance Metrics
# ==========================================================

@dataclass(slots=True)
class AIPerformanceMetrics:

    total_sessions: int = 0

    resolved_sessions: int = 0

    escalated_sessions: int = 0

    booking_sessions: int = 0

    average_duration: float = 0.0

    average_confidence: float = 0.0

    average_messages: float = 0.0

    resolution_rate: float = 0.0

    escalation_rate: float = 0.0

    booking_rate: float = 0.0


# ==========================================================
# AI Analytics Report
# ==========================================================

@dataclass(slots=True)
class AIAnalyticsReport:

    report_id: str

    business_id: str

    period: AIAnalyticsPeriod

    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metrics: AIPerformanceMetrics = field(
        default_factory=AIPerformanceMetrics
    )

    sessions: list[AISessionAnalytics] = field(
        default_factory=list
    )

    intents: list[IntentAnalytics] = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )

    # ======================================================
    # Helpers
    # ======================================================

    def add_session(
        self,
        session: AISessionAnalytics,
    ):

        self.sessions.append(session)

    def add_intent(
        self,
        intent: IntentAnalytics,
    ):

        self.intents.append(intent)

    @property
    def total_session_count(self) -> int:

        return len(self.sessions)

    @property
    def total_intent_count(self) -> int:

        return len(self.intents)