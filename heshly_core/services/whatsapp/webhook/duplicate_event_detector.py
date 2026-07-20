from datetime import datetime, timedelta

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
    """

    def __init__(
        self,
        retention_minutes: int = 30,
    ) -> None:

        self._retention = timedelta(
            minutes=retention_minutes
        )

        self._events: dict[
            str,
            datetime,
        ] = {}

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

        if event_id in self._events:

            return True

        self._events[event_id] = (
            datetime.utcnow()
        )

        return False

    def _event_id(
        self,
        event,
    ) -> str:

        return event.message_id

    def _cleanup(
        self,
    ) -> None:

        now = datetime.utcnow()

        expired = [

            event_id

            for event_id, timestamp

            in self._events.items()

            if now - timestamp
            > self._retention

        ]

        for event_id in expired:

            del self._events[event_id]