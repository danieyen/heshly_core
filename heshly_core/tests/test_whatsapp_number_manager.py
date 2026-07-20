from heshly_core.models.whatsapp_number import (
    WhatsAppNumber,
)

from heshly_core.services.communication.whatsapp_number_manager import (
    WhatsAppNumberManager,
)


def run_test():

    print("\n===================================")
    print("WhatsApp Number Manager Test")
    print("===================================\n")

    manager = WhatsAppNumberManager()

    main = WhatsAppNumber(

        number_id="num_001",

        tenant_id="tenant_001",

        phone_number="+254700000001",

        phone_number_id="meta001",

        display_name="Main Reception",

        primary=True,

    )

    manager.register(
        main
    )

    print("✅ Primary number registered")

    support = WhatsAppNumber(

        number_id="num_002",

        tenant_id="tenant_001",

        phone_number="+254700000002",

        phone_number_id="meta002",

        display_name="Support",

    )

    manager.register(
        support
    )

    print("✅ Secondary number registered")

    numbers = manager.numbers(
        "tenant_001"
    )

    assert len(numbers) == 2

    print("✅ Number listing")

    primary = manager.primary(
        "tenant_001"
    )

    assert primary is not None

    assert primary.phone_number == "+254700000001"

    print("✅ Primary number")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print(
        "\n🎉 WHATSAPP NUMBER MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()