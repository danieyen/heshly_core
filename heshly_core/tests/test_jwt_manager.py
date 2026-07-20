from heshly_core.services.security.jwt_manager import (
    JWTManager,
)


def run_test():

    print("\n================================")
    print("JWT Manager Test")
    print("================================\n")

    jwt = JWTManager(
        secret="super-secret-key"
    )

    token = jwt.create_token(

        user_id="user001",

        tenant_id="tenant001",

    )

    print("✅ Token created")

    assert jwt.validate(
        token
    )

    print("✅ Token validated")

    payload = jwt.payload(
        token
    )

    assert payload["sub"] == "user001"

    assert (
        payload["tenant_id"]
        ==
        "tenant001"
    )

    print("✅ Payload verified")

    assert (
        jwt.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check")

    print(
        "\n🎉 JWT SUPPORT TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()