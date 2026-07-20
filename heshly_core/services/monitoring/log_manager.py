from __future__ import annotations

from datetime import UTC, datetime


class LogManager:
    """
    Simple application log manager.
    """

    def __init__(self):

        self._logs = []

    def log(
        self,
        level: str,
        message: str,
    ):

        self._logs.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": level.upper(),
                "message": message,
            }
        )

    def info(
        self,
        message: str,
    ):

        self.log("INFO", message)

    def warning(
        self,
        message: str,
    ):

        self.log("WARNING", message)

    def error(
        self,
        message: str,
    ):

        self.log("ERROR", message)

    def entries(self):

        return list(self._logs)

    def count(self):

        return len(self._logs)

    def clear(self):

        self._logs.clear()

    def health(self):

        return {
            "status": "healthy",
            "entries": self.count(),
        }