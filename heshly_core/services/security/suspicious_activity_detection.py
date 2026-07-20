from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


# =====================================================
# Suspicious Activity
# =====================================================

@dataclass(slots=True)
class SuspiciousActivity:

    activity_id: str

    tenant_id: str | None

    user_id: str | None

    ip_address: str

    activity_type: str

    description: str

    first_seen: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_seen: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    occurrences: int = 1

    resolved: bool = False


# =====================================================
# Suspicious Activity Detection
# =====================================================

class SuspiciousActivityDetection:
    """
    Detects suspicious user and system activity.
    """

    def __init__(
        self,
        threshold: int = 5,
        window_minutes: int = 15,
    ):

        self.threshold = threshold

        self.window = timedelta(
            minutes=window_minutes
        )

        self._activities: dict[
            str,
            SuspiciousActivity
        ] = {}

        self._events = defaultdict(list)

    # =====================================================
    # Record Event
    # =====================================================

    def record_event(

        self,

        activity_id: str,

        tenant_id: str | None,

        user_id: str | None,

        ip_address: str,

        activity_type: str,

        description: str,

    ) -> bool:

        now = datetime.now(UTC)

        key = (

            ip_address,

            activity_type,

        )

        self._events[key] = [

            ts

            for ts in self._events[key]

            if now - ts <= self.window

        ]

        self._events[key].append(
            now
        )

        if len(self._events[key]) < self.threshold:

            return False

        activity = self._activities.get(
            activity_id
        )

        if activity is None:

            activity = SuspiciousActivity(

                activity_id=activity_id,

                tenant_id=tenant_id,

                user_id=user_id,

                ip_address=ip_address,

                activity_type=activity_type,

                description=description,

            )

            self._activities[
                activity_id
            ] = activity

        else:

            activity.occurrences += 1

            activity.last_seen = now

        return True

    # =====================================================
    # Queries
    # =====================================================

    def get(

        self,

        activity_id: str,

    ) -> SuspiciousActivity | None:

        return self._activities.get(
            activity_id
        )

    def list(self):

        return list(
            self._activities.values()
        )

    def unresolved(self):

        return [

            activity

            for activity in self._activities.values()

            if not activity.resolved

        ]

    # =====================================================
    # Resolution
    # =====================================================

    def resolve(

        self,

        activity_id: str,

    ) -> bool:

        activity = self.get(
            activity_id
        )

        if activity is None:

            return False

        activity.resolved = True

        return True

    # =====================================================
    # Management
    # =====================================================

    def clear(self):

        self._activities.clear()

        self._events.clear()

    def count(self):

        return len(
            self._activities
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "suspicious_activity_detection",

            "activities": self.count(),

            "status": "healthy",

        }