from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


class WhatsAppConversationOrchestrator:
    """
    Coordinates the complete lifecycle of an
    incoming WhatsApp conversation.

    This class connects the WhatsApp module
    with the AI Receptionist.
    """

    def process(
        self,
        event: IncomingMessageEvent,
    ) -> dict:
        """
        Process an incoming WhatsApp message.

        Future pipeline

        Customer
            ↓
        Conversation
            ↓
        AI Receptionist
            ↓
        Response Builder
            ↓
        Outgoing Sender
        """

        #
        # Future integrations
        #

        customer = {

            "phone_number": event.phone_number,

            "name": event.customer_name,

        }

        conversation = {

            "conversation_id": event.message_id,

            "channel": "whatsapp",

        }

        ai_request = {

            "text": event.text,

            "customer": customer,

            "conversation": conversation,

        }

        #
        # Future:
        #
        # response = conversation_engine.handle(
        #     ai_request
        # )
        #

        response = {

            "reply": (
                "Thank you for contacting us. "
                "Your message has been received."
            ),

            "intent": "unknown",

            "confidence": 1.0,

        }

        return {

            "customer": customer,

            "conversation": conversation,

            "request": ai_request,

            "response": response,

        }