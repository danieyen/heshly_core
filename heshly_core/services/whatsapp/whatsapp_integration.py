from __future__ import annotations

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)

from heshly_core.services.whatsapp.whatsapp_manager import (
    WhatsAppManager,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    WebhookVerificationRequest,
)


class WhatsAppIntegration:
    """
    High-level integration service for the
    entire WhatsApp module.

    This class is the entry point that other
    Heshly modules use when interacting with
    WhatsApp.
    """

    def __init__(
        self,
    ) -> None:

        self._manager = (
            WhatsAppManager()
        )

    def verify_webhook(
        self,
        configuration: WhatsAppConfiguration,
        request: WebhookVerificationRequest,
    ):

        return self._manager.verify_webhook(

            configuration,

            request,
        )

    def receive_webhook(
        self,
        payload: dict,
    ):

        return self._manager.process_webhook(
            payload
        )

    def process_conversation(
        self,
        configuration: WhatsAppConfiguration,
        event: IncomingMessageEvent,
    ):

        return self._manager.process_conversation(

            configuration,

            event,
        )

    def media_manager(
        self,
    ):

        return self._manager.media()

    @property
    def manager(
        self,
    ) -> WhatsAppManager:

        return self._manager