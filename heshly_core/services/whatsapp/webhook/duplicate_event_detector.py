from datetime import datetime, UTC, timedelta
import threading
from typing import Any

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    MediaEvent,
    MessageStatusEvent,
)


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if value.startswith("{") and value.endswith("}"):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


class WhatsAppDuplicateEventDetector:
    """
    Detects duplicate webhook events.

    Events are remembered for a limited
    period to prevent duplicate processing.

    Note: In-memory only. For multi-worker / multi-instance
    deployments replace with Redis/DB backed store.
    Tolerant to n8n sending JSON strings and nested bodies.
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
            | dict
            | str
        ),
    ) -> bool:

        self._cleanup()

        # Handle n8n sending dict or JSON string
        if isinstance(event, dict) or isinstance(event, str):
            data = _parse_json_if_string(event)
            if isinstance(data, dict):
                # Handle n8n $json.body nesting
                if "body" in data and isinstance(data["body"], dict) and "message_id" in data["body"]:
                    data = data["body"]
                if "json" in data and isinstance(data["json"], dict) and "message_id" in data["json"]:
                    data = data["json"]
                # Create minimal event for ID extraction
                message_id = data.get("message_id") or data.get("messageId") or data.get("id")
                if message_id:
                    event_id = str(message_id)
                    with self._lock:
                        if event_id in self._events:
                            return True
                        self._events[event_id] = datetime.now(UTC)
                    return False
                # Try Meta payload shape
                try:
                    from heshly_core.services.whatsapp.webhook.webhook_models import IncomingMessageEvent
                    parsed = IncomingMessageEvent.parse_meta_payload(data)
                    event_id = parsed.message_id
                    with self._lock:
                        if event_id in self._events:
                            return True
                        self._events[event_id] = datetime.now(UTC)
                    return False
                except Exception:
                    pass
            # Fallback to string handling
            if isinstance(event, str):
                event_id = event.strip()
                if event_id:
                    with self._lock:
                        if event_id in self._events:
                            return True
                        self._events[event_id] = datetime.now(UTC)
                    return False

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

    def has_seen(self, message_id: Any) -> bool:
        """Check without inserting. Handles JSON strings and dicts."""
        self._cleanup()
        if isinstance(message_id, dict):
            message_id = message_id.get("message_id") or message_id.get("messageId") or message_id.get("id") or ""
        message_id = str(message_id).strip() if message_id else ""
        if not message_id:
            return False
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
            # Try dict access
            if isinstance(event, dict):
                message_id = event.get("message_id") or event.get("messageId") or event.get("id")
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
