from heshly_core.models.api_key import (
    APIKeyScope,
)
from heshly_core.repositories.api_key_repository import (
    APIKeyRepository,
)
from heshly_core.services.security.api_key_manager import (
    APIKeyManager,
)


def run_test():

    print("\n================================")
    print("API Key Manager Test")
    print("================================\n")

    repository = APIKeyRepository()

    manager = APIKeyManager(
        repository
    )

    key, secret = manager.create_key(

        key_id="key001",

        tenant_id="tenant001",

        name="Production",

        scope=APIKeyScope.ADMIN,

        created_by="admin",

        expires_in_days=30,

    )

    print("✅ API key created")

    assert repository.count() == 1

    validated = manager.validate(
        secret
    )

    assert validated is not None

    print("✅ API key validated")

    assert manager.disable(
        "key001"
    )

    print("✅ API key disabled")

    assert manager.validate(
        secret
    ) is None

    print("✅ Disabled key rejected")

    assert manager.enable(
        "key001"
    )

    print("✅ API key enabled")

    assert manager.validate(
        secret
    ) is not None

    print("✅ Enabled key accepted")

    assert manager.revoke(
        "key001"
    )

    print("✅ API key revoked")

    assert manager.validate(
        secret
    ) is None

    print("✅ Revoked key rejected")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 API KEY MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()