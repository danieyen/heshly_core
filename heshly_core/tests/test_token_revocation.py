from heshly_core.services.security.token_revocation import (
    TokenRevocation,
)


def run_test():

    print("\n================================")
    print("Token Revocation Test")
    print("================================\n")

    service = TokenRevocation()

    token = "my-access-token"

    service.revoke(

        token=token,

        user_id="user001",

        tenant_id="tenant001",

        reason="User logout",

    )

    assert service.is_revoked(
        token
    )

    print("✅ Token revoked")

    revoked = service.get(
        token
    )

    assert revoked is not None

    print("✅ Revocation lookup")

    assert len(

        service.list_by_user(
            "user001"
        )

    ) == 1

    print("✅ User query")

    service.remove(
        token
    )

    assert not service.is_revoked(
        token
    )

    print("✅ Revocation removed")

    assert (

        service.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 TOKEN REVOCATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()