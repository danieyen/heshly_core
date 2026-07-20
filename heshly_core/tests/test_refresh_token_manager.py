from heshly_core.services.security.refresh_token_manager import (
    RefreshTokenManager,
)


def run_test():

    print("\n================================")
    print("Refresh Token Manager Test")
    print("================================\n")

    manager = RefreshTokenManager()

    token = manager.issue(

        user_id="user001",

        tenant_id="tenant001",

        session_id="session001",

    )

    assert manager.validate(
        token.token
    )

    print("✅ Token issued")

    replacement = manager.rotate(
        token.token
    )

    assert replacement is not None

    assert not manager.validate(
        token.token
    )

    assert manager.validate(
        replacement.token
    )

    print("✅ Token rotation")

    manager.revoke(
        replacement.token
    )

    assert not manager.validate(
        replacement.token
    )

    print("✅ Token revocation")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 REFRESH TOKEN MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()