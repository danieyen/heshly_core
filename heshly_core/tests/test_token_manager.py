from heshly_core.services.security.token_manager import (
    TokenManager,
)


def run_test():

    print("\n================================")
    print("Token Manager Test")
    print("================================\n")

    manager = TokenManager()

    access = manager.create_access_token(

        "user001",

        "tenant001",

    )

    refresh = manager.create_refresh_token(

        "user001",

        "tenant001",

    )

    print("✅ Tokens generated")

    assert manager.validate_access_token(
        access
    )

    assert manager.validate_refresh_token(
        refresh
    )

    print("✅ Validation")

    assert manager.access_token_data(
        access
    )["user_id"] == "user001"

    print("✅ Token lookup")

    manager.revoke_access_token(
        access
    )

    assert not manager.validate_access_token(
        access
    )

    print("✅ Access token revoked")

    manager.revoke_refresh_token(
        refresh
    )

    assert not manager.validate_refresh_token(
        refresh
    )

    print("✅ Refresh token revoked")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 TOKEN MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()