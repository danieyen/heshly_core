from heshly_core.services.security.encryption_service import (
    EncryptionService,
)
from heshly_core.services.security.secret_manager import (
    SecretManager,
)


def run_test():

    print("\n================================")
    print("Secret Manager Test")
    print("================================\n")

    encryption = EncryptionService(
        "master-secret"
    )

    manager = SecretManager(
        encryption
    )

    manager.set_secret(

        "whatsapp",

        "abc123",

    )

    assert manager.exists(
        "whatsapp"
    )

    print("✅ Secret stored")

    value = manager.get_secret(
        "whatsapp"
    )

    assert value == "abc123"

    print("✅ Secret retrieved")

    rotated = manager.rotate_secret(
        "whatsapp"
    )

    assert manager.get_secret(
        "whatsapp"
    ) == rotated

    print("✅ Secret rotated")

    assert manager.count() == 1

    print("✅ Secret count")

    assert manager.delete_secret(
        "whatsapp"
    )

    print("✅ Secret deleted")

    assert manager.count() == 0

    manager.clear()

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print("\n🎉 SECRET MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()