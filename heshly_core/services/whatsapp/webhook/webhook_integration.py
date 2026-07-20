from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)

from heshly_core.services.whatsapp.webhook.duplicate_event_detector import (
    WhatsAppDuplicateEventDetector,
)

from heshly_core.services.whatsapp.webhook.webhook_event_parser import (
    WhatsAppWebhookEventParser,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    WebhookProcessingResult,
    WebhookVerificationRequest,
    WebhookVerificationResult,
)

from heshly_core.services.whatsapp.webhook.webhook_router import (
    WhatsAppWebhookRouter,
)

from heshly_core.services.whatsapp.webhook.webhook_verification import (
    WhatsAppWebhookVerification,
)


class WhatsAppWebhookIntegration:
    """
    High-level entry point for all
    WhatsApp webhook processing.
    """

    def __init__(self) -> None:

        self._verification = (
            WhatsAppWebhookVerification()
        )

        self._parser = (
            WhatsAppWebhookEventParser()
        )

        self._duplicates = (
            WhatsAppDuplicateEventDetector()
        )

        self._router = (
            WhatsAppWebhookRouter()
        )

    def verify(
        self,
        configuration: WhatsAppConfiguration,
        request: WebhookVerificationRequest,
    ) -> WebhookVerificationResult:
        """
        Handles Meta's webhook
        verification challenge.
        """

        return self._verification.verify_challenge(
            configuration,
            request,
        )

    def process(
        self,
        payload: dict,
    ) -> WebhookProcessingResult:
        """
        Processes an incoming webhook.
        """

        event = self._parser.parse(
            payload
        )

        if self._duplicates.is_duplicate(
            event.payload
        ):

            return WebhookProcessingResult(

                success=True,

                event_type=event.event_type,

                message="Duplicate webhook ignored.",

                metadata={

                    "duplicate": True,

                },
            )

        return self._router.route(
            event
        )