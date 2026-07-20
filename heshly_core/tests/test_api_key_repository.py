from datetime import UTC, datetime, timedelta

from heshly_core.models.api_key import (
    APIKey,
)
from heshly_core.repositories.api_key_repository import (
    APIKeyRepository,
)


def run_test():

    print("\n================================")
    print("API Key Repository Test")
    print("================================\n")

    repository = APIKeyRepository()

    key = APIKey(

        key_id="key001",

        tenant_id="tenant001",

        name="Production",

        key_hash="hash001",

    )

    repository.save(key)

    assert repository.count() == 1
    print("✅ Saved")

    assert repository.exists("key001")
    print("✅ Exists")

    assert repository.get("key001") is not None
    print("✅ Retrieved")

    assert repository.get_by_hash(
        "hash001"
    ) is not None
    print("✅ Lookup by hash")

    assert len(
        repository.list_by_tenant(
            "tenant001"
        )
    ) == 1
    print("✅ Tenant lookup")

    assert len(
        repository.list_active()
    ) == 1
    print("✅ Active lookup")

    key.expires_at = (
        datetime.now(UTC)
        - timedelta(days=1)
    )

    assert len(
        repository.list_expired()
    ) == 1
    print("✅ Expired lookup")

    assert repository.delete(
        "key001"
    )
    print("✅ Deleted")

    assert repository.count() == 0

    repository.clear()

    print("\n🎉 API KEY REPOSITORY TEST PASSED\n")


if __name__ == "__main__":

    run_test()