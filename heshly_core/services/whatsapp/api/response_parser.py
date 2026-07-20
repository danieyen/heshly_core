from heshly_core.models.whatsapp import (
    WhatsAppContact,
    WhatsAppDirection,
    WhatsAppDeliveryStatus,
    WhatsAppMessage,
    WhatsAppMessageType,
)

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIError,
    CloudAPIResponse,
    CloudAPISuccess,
)


class WhatsAppResponseParser:
    """
    Converts Meta Cloud API responses
    into Heshly domain models.
    """

    def parse_send_message_response(
        self,
        response: CloudAPIResponse,
    ) -> CloudAPISuccess:

        body = response.body

        message_id = None

        messages = body.get(
            "messages",
            [],
        )

        if messages:

            message_id = messages[0].get(
                "id"
            )

        return CloudAPISuccess(

            success=(
                200 <= response.status_code < 300
            ),

            message_id=message_id,

            metadata=body,
        )

    def parse_error(
        self,
        response: CloudAPIResponse,
    ) -> CloudAPIError:

        error = response.body.get(
            "error",
            {},
        )

        return CloudAPIError(

            code=error.get(
                "code",
                -1,
            ),

            message=error.get(
                "message",
                "Unknown error.",
            ),

            error_type=error.get(
                "type",
            ),

            error_subcode=error.get(
                "error_subcode",
            ),

            fbtrace_id=error.get(
                "fbtrace_id",
            ),
        )

    def parse_webhook_message(
        self,
        payload: dict,
    ) -> WhatsAppMessage:
        """
        Converts a WhatsApp webhook payload
        into a Heshly WhatsAppMessage.
        """

        value = payload["entry"][0]["changes"][0]["value"]

        message = value["messages"][0]

        contact_data = value["contacts"][0]

        contact = WhatsAppContact(

            phone_number=contact_data["wa_id"],

            display_name=contact_data["profile"].get(
                "name"
            ),

            whatsapp_id=contact_data["wa_id"],
        )

        text = None

        message_type = WhatsAppMessageType.TEXT

        if message["type"] == "text":

            text = message["text"]["body"]

        return WhatsAppMessage(

            message_id=message["id"],

            conversation_id=message["id"],

            contact=contact,

            direction=WhatsAppDirection.INBOUND,

            message_type=message_type,

            text=text,

            status=WhatsAppDeliveryStatus.DELIVERED,
        )