from heshly_core.models.email_configuration import (
    EmailConfiguration,
)

from heshly_core.services.communication.email_configuration_manager import (
    EmailConfigurationManager,
)


def run_test():

    print("\n================================")
    print("Email Configuration Test")
    print("================================\n")

    manager = EmailConfigurationManager()

    configuration = EmailConfiguration(

        configuration_id="email_cfg_001",

        tenant_id="tenant_001",

        provider="smtp",

        sender_name="Smile Dental",

        sender_email="appointments@smiledental.com",

        smtp_host="smtp.example.com",

        smtp_port=587,

        username="appointments",

        password="secret",

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

        provider="sendgrid",

        enabled=True,

    )

    updated = manager.get(
        "tenant_001"
    )

    assert updated is not None

    assert updated.provider == "sendgrid"

    print("✅ Configuration updated")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print(
        "\n🎉 EMAIL CONFIGURATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()