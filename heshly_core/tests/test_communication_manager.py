from heshly_core.models.channel_route import (
    ChannelRoute,
    CommunicationChannel,
)

from heshly_core.models.communication_message import (
    CommunicationMessage,
)

from heshly_core.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)

from heshly_core.services.communication.channel_router import (
    ChannelRouter,
)

from heshly_core.services.communication.communication_manager import (
    CommunicationManager,
)


def run_test():

    print("\n================================")
    print("Communication Manager Test")
    print("================================\n")

    manager = CommunicationManager()

    manager.router.register(

        ChannelRoute(

            route_id="route001",

            tenant_id="tenant_001",

            event="appointment_reminder",

            preferred_channel=CommunicationChannel.WHATSAPP,

        )

    )

    manager.whatsapp.save(

        WhatsAppConfiguration(

            configuration_id="cfg001",

            tenant_id="tenant_001",

            business_account_id="123",

        )

    )

    message = CommunicationMessage(

        message_id="msg001",

        tenant_id="tenant_001",

        recipient="+254700000000",

        body="Reminder",

    )

    prepared = manager.prepare_message(

        "appointment_reminder",

        message,

    )

    assert prepared.channel == CommunicationChannel.WHATSAPP

    print("✅ Channel resolved")

    assert manager.validate_configuration(
        prepared
    )

    print("✅ Configuration validated")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 COMMUNICATION MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()