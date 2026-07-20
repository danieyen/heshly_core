from datetime import UTC, datetime, timedelta

from heshly_core.models.api_key import (
    APIKey,
    APIKeyScope,
    APIKeyStatus,
)


def run_test():

    print("\n================================")
    print("API Key Model Test")
    print("================================\n")

    key = APIKey(

        key_id="key001",

        tenant_id="tenant001",

        name="Production",

        key_hash="abc123hash",

        scope=APIKeyScope.ADMIN,

    )

    assert key.is_active

    print("✅ Active by default")

    key.disable()

    assert key.status == APIKeyStatus.DISABLED

    print("✅ Disabled")

    key.enable()

    assert key.status == APIKeyStatus.ACTIVE

    print("✅ Enabled")

    key.mark_used()

    assert key.last_used_at is not None

    print("✅ Usage tracked")

    key.expires_at = datetime.now(UTC) - timedelta(days=1)

    assert key.is_expired

    print("✅ Expiration detected")

    key.revoke()

    assert key.status == APIKeyStatus.REVOKED

    print("✅ Revoked")

    print("\n🎉 API KEY MODEL TEST PASSED\n")


if __name__ == "__main__":

    run_test()