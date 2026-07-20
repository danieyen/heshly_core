import os

from heshly_core.services.security.secrets_manager import (
    SecretsManager,
)


def test_secrets_management():

    print("\n================================")
    print("Secrets Management")
    print("================================\n")

    manager = SecretsManager()

    os.environ["JWT_SECRET"] = "jwt-secret"

    os.environ["DB_PASSWORD"] = "db-password"

    assert manager.exists(
        "JWT_SECRET"
    )

    assert (
        manager.get(
            "JWT_SECRET"
        )
        == "jwt-secret"
    )

    assert (
        manager.require(
            "DB_PASSWORD"
        )
        == "db-password"
    )

    assert (
        manager.get(
            "UNKNOWN",
            "default",
        )
        == "default"
    )

    print("JWT_SECRET ✓")

    print("DB_PASSWORD ✓")

    print("Secret lookup ✓")

    print("\n🎉 SECRETS MANAGEMENT PASSED\n")