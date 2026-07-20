from __future__ import annotations

from datetime import UTC, datetime


class ErrorTracker:
    """
    Tracks application errors.
    """

    def __init__(self):

        self._errors = []

    def capture(
        self,
        error: Exception,
    ):

        self._errors.append(
            {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def errors(self):

        return list(self._errors)

    def count(self):

        return len(self._errors)

    def clear(self):

        self._errors.clear()

    def health(self):

        return {
            "status": "healthy",
            "tracked_errors": self.count(),
        }