from heshly_core.services.whatsapp.webhook.webhook_models import (
    MediaEvent,
    WebhookEventType,
    WebhookProcessingResult,
)


class WhatsAppMediaEventProcessor:
    """
    Processes incoming WhatsApp media events.

    Future responsibilities:

    • Download media
    • Virus scanning
    • OCR
    • Speech-to-text
    • Image analysis
    • Attach media to conversations
    """

    def process(
        self,
        event: MediaEvent,
    ) -> WebhookProcessingResult:

        metadata = {

            "message_id": event.message_id,

            "media_id": event.media_id,

            "media_type": event.media_type,

            "mime_type": event.mime_type,

            "sha256": event.sha256,

            "caption": event.caption,

        }

        #
        # Future integrations:
        #
        # Media Downloader
        # File Storage
        # OCR Engine
        # Speech Recognition
        # Vision AI
        # Conversation Manager
        #

        return WebhookProcessingResult(

            success=True,

            event_type=WebhookEventType.MEDIA,

            message="Media event processed.",

            metadata=metadata,

        )