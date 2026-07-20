from heshly_core.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)

from heshly_core.services.communication.whatsapp_configuration_manager import (
    WhatsAppConfigurationManager,
)


def run_test():

    print("\n===================================")
    print("WhatsApp Configuration Test")
    print("===================================\n")

    manager = WhatsAppConfigurationManager()

    configuration = WhatsAppConfiguration(

        configuration_id="wa_cfg_001",

        tenant_id="tenant_001",

        business_account_id="123456789",

        phone_number_id="987654321",

        display_phone_number="+254700000000",

    )

    manager.save(
        configuration
    )

    print("✅ Configuration saved")

    stored = manager.get(
        "tenant_001"
    )

    assert stored is not None

    print("✅ Configuration retrieved")

    manager.update(

        "tenant_001",

        webhook_enabled=True,

        sandbox_mode=False,

    )

    updated = manager.get(
        "tenant_001"
    )

    assert updated is not None

    assert updated.webhook_enabled

    print("✅ Configuration updated")

    assert updated.sandbox_mode is False

    print("✅ Sandbox disabled")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print(
        "\n🎉 WHATSAPP CONFIGURATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()