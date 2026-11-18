from __future__ import annotations

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)

from heshly_core.repositories.whatsapp_activity_repository import (
    WhatsAppActivityRepository,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    MessageStatusEvent,
    WebhookEventType,
    WebhookProcessingResult,
)


class WhatsAppStatusUpdateProcessor:
    """
    Processes WhatsApp delivery/read/failure status updates.

    Meta webhook requests bypass normal tenant middleware.
    Tenant isolation is established explicitly from the
    WhatsAppConfiguration resolved by phone_number_id.
    """

    def process(
        self,
        event: MessageStatusEvent,
        configuration: WhatsAppConfiguration,
    ) -> WebhookProcessingResult:

        tenant_id = configuration.tenant_id

        if not tenant_id:
            return WebhookProcessingResult(
                success=False,
                event_type=WebhookEventType.STATUS,
                message="WhatsApp configuration has no tenant_id.",
                metadata={
                    "message_id": event.message_id,
                },
            )

        status = str(event.status).strip().lower()

        if not status:
            return WebhookProcessingResult(
                success=False,
                event_type=WebhookEventType.STATUS,
                message="Webhook status is required.",
                metadata={
                    "message_id": event.message_id,
                },
            )

        repository = WhatsAppActivityRepository(
            tenant_id=tenant_id,
        )

        activity = repository.update_status_by_message_id(
            message_id=event.message_id,
            status=status,
        )

        metadata = {
            "message_id": event.message_id,
            "recipient_id": event.recipient_id,
            "status": status,
            "timestamp": event.timestamp,
            "tenant_id": tenant_id,
            "updated": activity is not None,
        }

        if activity is None:
            return WebhookProcessingResult(
                success=True,
                event_type=WebhookEventType.STATUS,
                message=(
                    "Status received but no matching "
                    "WhatsApp activity was found."
                ),
                metadata=metadata,
            )

        return WebhookProcessingResult(
            success=True,
            event_type=WebhookEventType.STATUS,
            message="WhatsApp activity status updated.",
            metadata=metadata,
        )
