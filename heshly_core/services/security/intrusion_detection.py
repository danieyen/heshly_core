from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from collections import defaultdict


# =====================================================
# Threat Levels
# =====================================================

class ThreatLevel:

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    CRITICAL = "critical"


# =====================================================
# Intrusion Event
# =====================================================

@dataclass(slots=True)
class IntrusionEvent:

    event_id: str

    tenant_id: str | None

    user_id: str | None

    ip_address: str

    event_type: str

    description: str

    threat_level: str

    detected_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    occurrences: int = 1

    resolved: bool = False


# =====================================================
# Intrusion Detection
# =====================================================

class IntrusionDetection:
    """
    Detects suspicious patterns that may
    indicate an intrusion attempt.

    Examples:
    - Excessive failed logins
    - Token abuse
    - API abuse
    - Credential stuffing
    """

    def __init__(

        self,

        threshold: int = 10,

        window_minutes: int = 10,

    ):

        self.threshold = threshold

        self.window = timedelta(
            minutes=window_minutes
        )

        self._events: dict[
            str,
            IntrusionEvent,
        ] = {}

        self._history = defaultdict(list)

    # =====================================================
    # Detection
    # =====================================================

    def record(

        self,

        event_id: str,

        tenant_id: str | None,

        user_id: str | None,

        ip_address: str,

        event_type: str,

        description: str,

    ) -> bool:

        now = datetime.now(UTC)

        key = (

            ip_address,

            event_type,

        )

        self._history[key] = [

            timestamp

            for timestamp

            in self._history[key]

            if now - timestamp <= self.window

        ]

        self._history[key].append(
            now
        )

        if len(
            self._history[key]
        ) < self.threshold:

            return False

        if event_id in self._events:

            event = self._events[
                event_id
            ]

            event.occurrences += 1

            event.detected_at = now

        else:

            self._events[
                event_id
            ] = IntrusionEvent(

                event_id=event_id,

                tenant_id=tenant_id,

                user_id=user_id,

                ip_address=ip_address,

                event_type=event_type,

                description=description,

                threat_level=ThreatLevel.HIGH,

            )

        return True

    # =====================================================
    # Queries
    # =====================================================

    def get(

        self,

        event_id: str,

    ) -> IntrusionEvent | None:

        return self._events.get(
            event_id
        )

    def list(self):

        return list(
            self._events.values()
        )

    def unresolved(self):

        return [

            event

            for event

            in self._events.values()

            if not event.resolved

        ]

    def by_threat_level(

        self,

        level: str,

    ):

        return [

            event

            for event

            in self._events.values()

            if event.threat_level == level

        ]

    # =====================================================
    # Resolution
    # =====================================================

    def resolve(

        self,

        event_id: str,

    ) -> bool:

        event = self.get(
            event_id
        )

        if event is None:

            return False

        event.resolved = True

        return True

    # =====================================================
    # Management
    # =====================================================

    def clear(self):

        self._events.clear()

        self._history.clear()

    def count(self):

        return len(
            self._events
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "intrusion_detection",

            "events": self.count(),

            "status": "healthy",

        }