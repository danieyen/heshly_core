from heshly_core.services.security.encryption_service import (
    EncryptionService,
)
from heshly_core.services.security.secret_manager import (
    SecretManager,
)
from heshly_core.services.security.secure_configuration import (
    SecureConfiguration,
)


def run_test():

    print("\n================================")
    print("Secure Configuration Test")
    print("================================\n")

    encryption = EncryptionService(
        "master-key"
    )

    secrets = SecretManager(
        encryption
    )

    config = SecureConfiguration(
        secrets
    )

    # =====================================================
    # Configuration
    # =====================================================

    config.set(
        "timezone",
        "Africa/Nairobi",
    )

    config.set(
        "currency",
        "KES",
    )

    assert config.exists(
        "timezone"
    )

    assert config.get(
        "timezone"
    ) == "Africa/Nairobi"

    print("✅ Configuration stored")

    # =====================================================
    # Secrets
    # =====================================================

    config.set_secret(

        "openai_api_key",

        "sk-demo-secret",

    )

    assert (

        config.get_secret(
            "openai_api_key"
        )

        ==

        "sk-demo-secret"

    )

    print("✅ Secret stored securely")

    rotated = config.rotate_secret(
        "openai_api_key"
    )

    assert (

        config.get_secret(
            "openai_api_key"
        )

        ==

        rotated

    )

    print("✅ Secret rotated")

    # =====================================================
    # Export
    # =====================================================

    exported = config.export()

    assert exported["timezone"] == (
        "Africa/Nairobi"
    )

    assert (
        "openai_api_key"
        not in exported
    )

    print("✅ Secrets excluded from export")

    # =====================================================
    # Delete
    # =====================================================

    assert config.delete(
        "currency"
    )

    assert config.delete_secret(
        "openai_api_key"
    )

    print("✅ Configuration removed")

    # =====================================================
    # Health
    # =====================================================

    assert (

        config.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 SECURE CONFIGURATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()