from heshly_core.services.whatsapp.webhook.webhook_models import (
    MessageStatusEvent,
    WebhookEventType,
    WebhookProcessingResult,
)


class WhatsAppStatusUpdateProcessor:
    """
    Processes WhatsApp message
    status updates.

    Future responsibilities:

    • Update message status
    • Update conversation timeline
    • Trigger delivery analytics
    • Notify business rules
    """

    def process(
        self,
        event: MessageStatusEvent,
    ) -> WebhookProcessingResult:

        metadata = {

            "message_id": event.message_id,

            "recipient_id": event.recipient_id,

            "status": event.status,

            "timestamp": event.timestamp,

        }

        #
        # Future:
        #
        # Message Store
        # Conversation Store
        # Analytics
        #

        return WebhookProcessingResult(

            success=True,

            event_type=WebhookEventType.STATUS,

            message="Status update processed.",

            metadata=metadata,

        )