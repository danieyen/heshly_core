from datetime import datetime, UTC, timedelta
import threading

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    MediaEvent,
    MessageStatusEvent,
)


class WhatsAppDuplicateEventDetector:
    """
    Detects duplicate webhook events.

    Events are remembered for a limited
    period to prevent duplicate processing.

    Note: In-memory only. For multi-worker / multi-instance
    deployments replace with Redis/DB backed store.
    """

    def __init__(
        self,
        retention_minutes: int = 30,
    ) -> None:

        if retention_minutes <= 0:
            raise ValueError("retention_minutes must be > 0")

        self._retention = timedelta(
            minutes=retention_minutes
        )

        self._events: dict[
            str,
            datetime,
        ] = {}

        self._lock = threading.Lock()

    def is_duplicate(
        self,
        event: (
            IncomingMessageEvent
            | MessageStatusEvent
            | MediaEvent
        ),
    ) -> bool:

        self._cleanup()

        event_id = self._event_id(
            event
        )

        with self._lock:
            if event_id in self._events:
                return True

            self._events[event_id] = (
                datetime.now(UTC)
            )

        return False

    def has_seen(self, message_id: str) -> bool:
        """Check without inserting."""
        self._cleanup()
        with self._lock:
            return message_id in self._events

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def _event_id(
        self,
        event,
    ) -> str:

        message_id = getattr(
            event,
            "message_id",
            None,
        )

        if not message_id:
            raise ValueError(
                "Webhook event has no message_id."
            )

        return str(message_id)

    def _cleanup(
        self,
    ) -> None:

        now = datetime.now(UTC)

        expired = []

        with self._lock:
            for event_id, timestamp in list(self._events.items()):
                # Ensure timestamp is timezone-aware for comparison
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=UTC)
                if now - timestamp > self._retention:
                    expired.append(event_id)

            for event_id in expired:
                del self._events[event_id]
