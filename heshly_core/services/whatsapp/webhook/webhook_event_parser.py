from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
    MediaEvent,
    MessageStatusEvent,
    WebhookEvent,
    WebhookEventType,
)


class WhatsAppWebhookEventParser:
    """
    Converts Meta webhook payloads into
    Heshly webhook models.
    """

    def parse(
        self,
        payload: dict,
    ) -> WebhookEvent:

        value = payload["entry"][0]["changes"][0]["value"]

        if "messages" in value:

            message = value["messages"][0]

            if message["type"] == "text":

                return WebhookEvent(

                    event_type=WebhookEventType.MESSAGE,

                    payload=self.parse_message(
                        payload
                    ),
                )

            return WebhookEvent(

                event_type=WebhookEventType.MEDIA,

                payload=self.parse_media(
                    payload
                ),
            )

        if "statuses" in value:

            return WebhookEvent(

                event_type=WebhookEventType.STATUS,

                payload=self.parse_status(
                    payload
                ),
            )

        return WebhookEvent(

            event_type=WebhookEventType.UNKNOWN,

            payload=payload,
        )

    def parse_message(
        self,
        payload: dict,
    ) -> IncomingMessageEvent:

        value = payload["entry"][0]["changes"][0]["value"]

        contact = value["contacts"][0]

        message = value["messages"][0]

        return IncomingMessageEvent(

            message_id=message["id"],

            phone_number=contact["wa_id"],

            customer_name=contact["profile"].get(
                "name"
            ),

            message_type=message["type"],

            text=message["text"].get(
                "body"
            ),

            timestamp=message.get(
                "timestamp"
            ),
        )

    def parse_status(
        self,
        payload: dict,
    ) -> MessageStatusEvent:

        value = payload["entry"][0]["changes"][0]["value"]

        status = value["statuses"][0]

        return MessageStatusEvent(

            message_id=status["id"],

            recipient_id=status[
                "recipient_id"
            ],

            status=status["status"],

            timestamp=status.get(
                "timestamp"
            ),
        )

    def parse_media(
        self,
        payload: dict,
    ) -> MediaEvent:

        value = payload["entry"][0]["changes"][0]["value"]

        message = value["messages"][0]

        media = message[message["type"]]

        return MediaEvent(

            message_id=message["id"],

            media_id=media["id"],

            media_type=message["type"],

            mime_type=media.get(
                "mime_type"
            ),

            sha256=media.get(
                "sha256"
            ),

            caption=media.get(
                "caption"
            ),
        )