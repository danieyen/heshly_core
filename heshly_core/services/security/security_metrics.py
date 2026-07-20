from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


# =====================================================
# Security Metric
# =====================================================

@dataclass(slots=True)
class SecurityMetric:
    """
    Represents a single security metric.
    """

    name: str

    value: int = 0

    description: str = ""

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# =====================================================
# Security Metrics
# =====================================================

class SecurityMetrics:
    """
    Collects security metrics across the platform.

    Other security modules can update these
    counters to provide a centralized view of
    the system's security posture.
    """

    def __init__(self):

        self._metrics: dict[
            str,
            SecurityMetric,
        ] = {}

    # =====================================================
    # Metric Management
    # =====================================================

    def register(

        self,

        name: str,

        description: str = "",

        initial_value: int = 0,

    ) -> SecurityMetric:

        metric = SecurityMetric(

            name=name,

            value=initial_value,

            description=description,

        )

        self._metrics[name] = metric

        return metric

    def get(

        self,

        name: str,

    ) -> SecurityMetric | None:

        return self._metrics.get(
            name
        )

    def exists(

        self,

        name: str,

    ) -> bool:

        return name in self._metrics

    # =====================================================
    # Updates
    # =====================================================

    def increment(

        self,

        name: str,

        amount: int = 1,

    ):

        if not self.exists(name):

            self.register(name)

        metric = self._metrics[name]

        metric.value += amount

        metric.updated_at = datetime.now(
            UTC
        )

    def decrement(

        self,

        name: str,

        amount: int = 1,

    ):

        if not self.exists(name):

            self.register(name)

        metric = self._metrics[name]

        metric.value -= amount

        metric.updated_at = datetime.now(
            UTC
        )

    def set(

        self,

        name: str,

        value: int,

    ):

        if not self.exists(name):

            self.register(name)

        metric = self._metrics[name]

        metric.value = value

        metric.updated_at = datetime.now(
            UTC
        )

    # =====================================================
    # Queries
    # =====================================================

    def value(

        self,

        name: str,

    ) -> int:

        metric = self.get(name)

        if metric is None:

            return 0

        return metric.value

    def list(self):

        return list(
            self._metrics.values()
        )

    def count(self):

        return len(
            self._metrics
        )

    # =====================================================
    # Export
    # =====================================================

    def snapshot(self):

        return {

            metric.name: metric.value

            for metric

            in self._metrics.values()

        }

    # =====================================================
    # Management
    # =====================================================

    def clear(self):

        self._metrics.clear()

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "security_metrics",

            "metrics": self.count(),

            "status": "healthy",

        }