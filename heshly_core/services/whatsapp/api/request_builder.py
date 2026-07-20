from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppMessage,
    WhatsAppMessageType,
)

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIRequest,
)


class WhatsAppRequestBuilder:
    """
    Converts Heshly WhatsApp models
    into Meta Cloud API requests.
    """

    def build_send_message_request(
        self,
        configuration: WhatsAppConfiguration,
        message: WhatsAppMessage,
    ) -> CloudAPIRequest:

        endpoint = (
            f"/{configuration.api_version}/"
            f"{configuration.phone_number_id}/messages"
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.contact.phone_number,
        }

        if message.message_type == WhatsAppMessageType.TEXT:

            payload["type"] = "text"

            payload["text"] = {
                "preview_url": False,
                "body": message.text or "",
            }

        else:

            raise NotImplementedError(
                f"{message.message_type.value} "
                "messages are not yet supported."
            )

        return CloudAPIRequest(

            method="POST",

            endpoint=endpoint,

            payload=payload,
        )