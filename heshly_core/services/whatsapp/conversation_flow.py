from __future__ import annotations

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppContact,
    WhatsAppDirection,
    WhatsAppMessage,
    WhatsAppMessageType,
)

from heshly_core.services.whatsapp.conversation_orchestrator import (
    WhatsAppConversationOrchestrator,
)

from heshly_core.services.whatsapp.outgoing_message_sender import (
    WhatsAppOutgoingMessageSender,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


class WhatsAppConversationFlow:
    """
    Complete WhatsApp conversation flow.

    Receives an incoming WhatsApp message,
    coordinates the AI conversation,
    and sends the reply.
    """

    def __init__(
        self,
    ) -> None:

        self._orchestrator = (
            WhatsAppConversationOrchestrator()
        )

        self._sender = (
            WhatsAppOutgoingMessageSender()
        )

    def process(
        self,
        configuration: WhatsAppConfiguration,
        event: IncomingMessageEvent,
    ) -> dict:

        orchestration = (
            self._orchestrator.process(
                event
            )
        )

        reply = orchestration[
            "response"
        ][
            "reply"
        ]

        contact = WhatsAppContact(

            phone_number=event.phone_number,

            display_name=(
                event.customer_name
            ),
        )

        outgoing = WhatsAppMessage(

            message_id=event.message_id,

            conversation_id=event.message_id,

            contact=contact,

            direction=(
                WhatsAppDirection.OUTBOUND
            ),

            message_type=(
                WhatsAppMessageType.TEXT
            ),

            text=reply,
        )

        send_result = self._sender.send(

            configuration,

            outgoing,
        )

        return {

            "orchestration": orchestration,

            "send_result": send_result,

        }