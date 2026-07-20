from heshly_core.models.sms_configuration import (
    SMSConfiguration,
    SMSProvider,
)

from heshly_core.services.communication.sms_configuration_manager import (
    SMSConfigurationManager,
)


def run_test():

    print("\n==============================")
    print("SMS Configuration Test")
    print("==============================\n")

    manager = SMSConfigurationManager()

    configuration = SMSConfiguration(

        configuration_id="sms_cfg_001",

        tenant_id="tenant_001",

        provider=SMSProvider.AFRICASTALKING,

        sender_id="HESHLY",

        api_key="sample_key",

        api_secret="sample_secret",

        username="sandbox",

        enabled=True,

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

        provider=SMSProvider.TWILIO,

        sandbox_mode=False,

    )

    updated = manager.get(
        "tenant_001"
    )

    assert updated is not None
    assert updated.provider == SMSProvider.TWILIO

    print("✅ Configuration updated")

    assert updated.sandbox_mode is False

    print("✅ Sandbox disabled")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 SMS CONFIGURATION TEST PASSED\n")


if __name__ == "__main__":

    run_test()