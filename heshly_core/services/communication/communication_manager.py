from __future__ import annotations

from heshly_core.models.communication_message import (
    CommunicationMessage,
)

from heshly_core.services.communication.channel_router import (
    ChannelRouter,
)

from heshly_core.services.communication.email_configuration_manager import (
    EmailConfigurationManager,
)

from heshly_core.services.communication.sms_configuration_manager import (
    SMSConfigurationManager,
)

from heshly_core.services.communication.whatsapp_configuration_manager import (
    WhatsAppConfigurationManager,
)


class CommunicationManager:
    """
    Communication Manager.

    Central communication orchestrator.
    """

    def __init__(self):

        self.router = ChannelRouter()

        self.whatsapp = (
            WhatsAppConfigurationManager()
        )

        self.email = (
            EmailConfigurationManager()
        )

        self.sms = (
            SMSConfigurationManager()
        )

    # =====================================================
    # Routing
    # =====================================================

    def resolve_channel(
        self,
        tenant_id: str,
        event: str,
    ):

        return self.router.resolve(
            tenant_id,
            event,
        )

    # =====================================================
    # Message
    # =====================================================

    def prepare_message(
        self,
        event: str,
        message: CommunicationMessage,
    ) -> CommunicationMessage:

        channel = self.resolve_channel(

            message.tenant_id,

            event,

        )

        message.channel = channel

        return message

    # =====================================================
    # Validation
    # =====================================================

    def validate_configuration(
        self,
        message: CommunicationMessage,
    ) -> bool:

        if message.channel is None:

            return False

        if message.channel.value == "whatsapp":

            return (

                self.whatsapp.get(
                    message.tenant_id
                )
                is not None
            )

        if message.channel.value == "email":

            return (

                self.email.get(
                    message.tenant_id
                )
                is not None
            )

        if message.channel.value == "sms":

            return (

                self.sms.get(
                    message.tenant_id
                )
                is not None
            )

        return False

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "communication_manager",

            "status": "healthy",

        }