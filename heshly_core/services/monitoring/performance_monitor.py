from __future__ import annotations

from datetime import UTC, datetime
import time


class PerformanceMonitor:
    """
    Tracks basic application performance metrics.
    """

    def __init__(self):

        self._metrics = {
            "requests": 0,
            "average_response_time": 0.0,
            "last_response_time": 0.0,
            "start_time": datetime.now(UTC),
        }

    def record_request(
        self,
        response_time: float,
    ):

        self._metrics["requests"] += 1

        self._metrics["last_response_time"] = response_time

        count = self._metrics["requests"]

        avg = self._metrics["average_response_time"]

        self._metrics["average_response_time"] = (
            ((avg * (count - 1)) + response_time)
            / count
        )

    def metrics(self):

        return dict(self._metrics)

    def uptime_seconds(self):

        return (
            datetime.now(UTC)
            - self._metrics["start_time"]
        ).total_seconds()

    def health(self):

        return {
            "status": "healthy",
            "requests": self._metrics["requests"],
            "uptime": self.uptime_seconds(),
        }