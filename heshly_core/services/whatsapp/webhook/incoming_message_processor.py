from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    WebhookProcessingResult,
    WebhookEventType,
)


class WhatsAppIncomingMessageProcessor:
    """
    Processes incoming WhatsApp messages
    and hands them to the AI Receptionist.
    """

    def process(
        self,
        event: IncomingMessageEvent,
    ) -> WebhookProcessingResult:

        metadata = {

            "message_id": event.message_id,

            "phone_number": event.phone_number,

            "customer_name": event.customer_name,

            "message_type": event.message_type,

            "text": event.text,

            "timestamp": event.timestamp,

        }

        #
        # Future integration:
        #
        # Conversation Manager
        # AI Receptionist
        # Memory
        # Booking Engine
        #

        return WebhookProcessingResult(

            success=True,

            event_type=WebhookEventType.MESSAGE,

            message="Incoming message processed.",

            metadata=metadata,

        )