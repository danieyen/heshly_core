from __future__ import annotations

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppMessage,
)

from heshly_core.services.whatsapp.conversation_flow import (
    WhatsAppConversationFlow,
)

from heshly_core.services.whatsapp.media_manager import (
    WhatsAppMediaManager,
)

from heshly_core.services.whatsapp.outgoing_message_sender import (
    WhatsAppOutgoingMessageSender,
)

from heshly_core.services.whatsapp.webhook.webhook_integration import (
    WhatsAppWebhookIntegration,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    WebhookProcessingResult,
    WebhookVerificationRequest,
    WebhookVerificationResult,
)


class WhatsAppManager:
    """
    High-level entry point for the
    WhatsApp module.

    All other modules should interact
    with WhatsApp through this class.
    """

    def __init__(
        self,
    ) -> None:

        self._webhooks = (
            WhatsAppWebhookIntegration()
        )

        self._conversation_flow = (
            WhatsAppConversationFlow()
        )

        self._media = (
            WhatsAppMediaManager()
        )

        self._sender = (
            WhatsAppOutgoingMessageSender()
        )

    def verify_webhook(
        self,
        configuration: WhatsAppConfiguration,
        request: WebhookVerificationRequest,
    ) -> WebhookVerificationResult:

        return self._webhooks.verify(

            configuration,

            request,
        )

    def process_webhook(
        self,
        payload: dict,
    ) -> WebhookProcessingResult:

        return self._webhooks.process(
            payload
        )

    def process_conversation(
        self,
        configuration: WhatsAppConfiguration,
        event: IncomingMessageEvent,
    ) -> dict:

        return self._conversation_flow.process(

            configuration,

            event,
        )

    def send_message(
        self,
        configuration: WhatsAppConfiguration,
        message: WhatsAppMessage,
    ):

        return self._sender.send(

            configuration,

            message,
        )

    def media(
        self,
    ) -> WhatsAppMediaManager:

        return self._media