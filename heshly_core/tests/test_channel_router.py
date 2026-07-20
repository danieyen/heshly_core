from heshly_core.models.channel_route import (
    ChannelRoute,
    CommunicationChannel,
)

from heshly_core.services.communication.channel_router import (
    ChannelRouter,
)


def run_test():

    print("\n==============================")
    print("Channel Router Test")
    print("==============================\n")

    router = ChannelRouter()

    route = ChannelRoute(

        route_id="route_001",

        tenant_id="tenant_001",

        event="appointment_reminder",

        preferred_channel=CommunicationChannel.WHATSAPP,

        fallback_channels=[

            CommunicationChannel.SMS,

            CommunicationChannel.EMAIL,

        ],

    )

    router.register(
        route
    )

    print("✅ Route registered")

    channel = router.resolve(

        "tenant_001",

        "appointment_reminder",

    )

    assert channel == CommunicationChannel.WHATSAPP

    print("✅ Preferred channel resolved")

    fallbacks = router.fallback_channels(

        "tenant_001",

        "appointment_reminder",

    )

    assert len(fallbacks) == 2

    print("✅ Fallback channels")

    assert router.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 CHANNEL ROUTER TEST PASSED\n")


if __name__ == "__main__":

    run_test()