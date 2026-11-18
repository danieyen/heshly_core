from __future__ import annotations

from heshly_core.models.whatsapp import WhatsAppConfiguration

from heshly_core.services.whatsapp.webhook.incoming_message_processor import (
    WhatsAppIncomingMessageProcessor,
)

from heshly_core.services.whatsapp.webhook.media_event_processor import (
    WhatsAppMediaEventProcessor,
)

from heshly_core.services.whatsapp.webhook.status_update_processor import (
    WhatsAppStatusUpdateProcessor,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    WebhookEvent,
    WebhookEventType,
    WebhookProcessingResult,
)


class WhatsAppWebhookRouter:
    """
    Routes webhook events to the appropriate processor.
    """

    def __init__(self) -> None:
        self._message_processor = (
            WhatsAppIncomingMessageProcessor()
        )

        self._status_processor = (
            WhatsAppStatusUpdateProcessor()
        )

        self._media_processor = (
            WhatsAppMediaEventProcessor()
        )

    def route(
        self,
        event: WebhookEvent,
        configuration: WhatsAppConfiguration,
    ) -> WebhookProcessingResult:

        if event.event_type == WebhookEventType.MESSAGE:
            return self._message_processor.process(
                event.payload,
                configuration,
            )

        if event.event_type == WebhookEventType.STATUS:
            return self._status_processor.process(
                event.payload,
                configuration,
            )

        if event.event_type == WebhookEventType.MEDIA:
            return self._media_processor.process(
                event.payload
            )

        return WebhookProcessingResult(
            success=False,
            event_type=WebhookEventType.UNKNOWN,
            message="Unsupported webhook event.",
            metadata={},
        )
