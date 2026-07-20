from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.authentication_middleware import (
    AuthenticationMiddleware,
)


def run_test():

    print("\n================================")
    print("Authentication Middleware Test")
    print("================================\n")


    auth = AuthenticationMiddleware()


    user = AuthUser(

        user_id="user001",

        email="admin@smiledental.com",

        tenant_id="tenant001",

    )


    auth.register_token(

        "token123",

        user,

    )


    print("✅ Token registered")


    authenticated = auth.authenticate(
        "token123"
    )


    assert authenticated is not None

    assert (
        authenticated.user_id
        ==
        "user001"
    )


    print("✅ User authenticated")


    required = auth.require(
        "token123"
    )


    assert required.email == (
        "admin@smiledental.com"
    )


    print("✅ Authentication required")


    try:

        auth.require(
            "invalid-token"
        )

        assert False


    except PermissionError:

        print(
            "✅ Invalid token rejected"
        )


    assert (
        auth.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health check")


    print(
        "\n🎉 AUTHENTICATION MIDDLEWARE TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()