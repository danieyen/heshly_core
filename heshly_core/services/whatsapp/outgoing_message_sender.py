from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppMessage,
)

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIError,
    CloudAPISuccess,
)

from heshly_core.services.whatsapp.api.cloud_api_client import (
    WhatsAppCloudAPIClient,
)


class WhatsAppOutgoingMessageSender:
    """
    Sends outgoing WhatsApp messages.

    This is the high-level sending service
    used by the rest of Heshly.
    """

    def __init__(
        self,
    ) -> None:

        self._client = (
            WhatsAppCloudAPIClient()
        )

    def send(
        self,
        configuration: WhatsAppConfiguration,
        message: WhatsAppMessage,
    ) -> CloudAPISuccess | CloudAPIError:
        """
        Sends a WhatsApp message.
        """

        #
        # Future responsibilities
        #
        # Logging
        # Queueing
        # Rate limiting
        # Delivery tracking
        #

        return self._client.send_message(

            configuration,

            message,
        )