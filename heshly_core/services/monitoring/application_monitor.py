from __future__ import annotations

from datetime import UTC, datetime


class ApplicationMonitor:
    """
    Monitors overall application health.
    """

    def health(self) -> dict:

        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime": "running",
        }

    def metrics(self) -> dict:

        return {
            "cpu": 0,
            "memory": 0,
            "requests": 0,
            "errors": 0,
        }

    def status(self) -> str:

        return "running"