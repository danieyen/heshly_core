from __future__ import annotations

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)

from heshly_core.repositories.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepository,
)

from heshly_core.services.whatsapp.webhook.duplicate_event_detector import (
    WhatsAppDuplicateEventDetector,
)

from heshly_core.services.whatsapp.webhook.webhook_event_parser import (
    WhatsAppWebhookEventParser,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    WebhookEventType,
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
    High-level entry point for WhatsApp webhook processing.

    Responsibilities:

    - Verify Meta webhook challenges.
    - Resolve tenant configuration.
    - Parse webhook payloads.
    - Reject duplicate events.
    - Route events.
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

        self._configurations = (
            WhatsAppConfigurationRepository()
        )

    def verify(
        self,
        configuration: WhatsAppConfiguration,
        request: WebhookVerificationRequest,
    ) -> WebhookVerificationResult:

        return self._verification.verify_challenge(
            configuration,
            request,
        )

    def process(
        self,
        payload: dict,
    ) -> WebhookProcessingResult:

        configuration = (
            self.configuration_for_payload(
                payload
            )
        )

        if configuration is None:
            return WebhookProcessingResult(
                success=False,
                event_type=WebhookEventType.UNKNOWN,
                message=(
                    "WhatsApp configuration not found."
                ),
                metadata={},
            )

        event = self._parser.parse(payload)

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
            event,
            configuration,
        )

    def configuration_for_payload(
        self,
        payload: dict,
    ) -> WhatsAppConfiguration | None:

        phone_number_id = (
            self._phone_number_id(payload)
        )

        if not phone_number_id:
            return None

        return (
            self._configurations
            .get_by_phone_number_id(
                phone_number_id
            )
        )

    @staticmethod
    def _phone_number_id(
        payload: dict,
    ) -> str | None:

        try:
            value = (
                payload["entry"][0]
                ["changes"][0]
                ["value"]
            )

            metadata = value.get(
                "metadata"
            ) or {}

            return metadata.get(
                "phone_number_id"
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ):
            return None
