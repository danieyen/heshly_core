from __future__ import annotations

from heshly_core.models.whatsapp import WhatsAppConfiguration

from heshly_core.services.whatsapp.conversation_flow import (
    WhatsAppConversationFlow,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    WebhookEventType,
    WebhookProcessingResult,
)


class WhatsAppIncomingMessageProcessor:
    """
    Processes incoming WhatsApp messages
    and hands them to the AI Receptionist.
    """

    def __init__(self) -> None:
        self._conversation_flow = (
            WhatsAppConversationFlow()
        )

    def process(
        self,
        event: IncomingMessageEvent,
        configuration: WhatsAppConfiguration,
    ) -> WebhookProcessingResult:

        if not event.text:
            return WebhookProcessingResult(
                success=True,
                event_type=WebhookEventType.MESSAGE,
                message="Non-text WhatsApp message received.",
                metadata={
                    "message_id": event.message_id,
                    "phone_number": event.phone_number,
                    "message_type": event.message_type,
                },
            )

        tenant_id = (
            configuration.tenant_id
        )

        event.tenant_id = tenant_id

        result = self._conversation_flow.process(
            event,
            tenant_id=tenant_id,
            configuration=configuration,
        )

        orchestration = (
            result.get("orchestration")
            or {}
        )

        response = (
            orchestration.get("response")
            or {}
        )

        send_result = result.get(
            "send_result"
        )

        metadata = {
            "message_id": event.message_id,
            "phone_number": event.phone_number,
            "customer_name": event.customer_name,
            "message_type": event.message_type,
            "text": event.text,
            "timestamp": event.timestamp,
            "phone_number_id": event.phone_number_id,
            "tenant_id": tenant_id,
            "reply": response.get("reply"),
            "intent": response.get("intent"),
            "confidence": response.get("confidence"),
            "action": response.get("action"),
            "send_result": (
                getattr(
                    send_result,
                    "__dict__",
                    None,
                )
                if send_result is not None
                else None
            ),
        }

        return WebhookProcessingResult(
            success=True,
            event_type=WebhookEventType.MESSAGE,
            message="Incoming message processed.",
            metadata=metadata,
        )
