from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.authentication_service import (
    AuthenticationService,
)


def run_test():

    print("\n================================")
    print("Authentication Service Test")
    print("================================\n")


    service = AuthenticationService()


    user = AuthUser(

        user_id="user001",

        tenant_id="tenant001",

        email="admin@smiledental.com",

        first_name="John",

        last_name="Doe",

    )


    service.register(

        user,

        "SecurePass123!",

    )


    print("✅ User registered")


    authenticated = service.authenticate(

        "admin@smiledental.com",

        "SecurePass123!",

    )


    assert authenticated is not None

    print("✅ Authentication successful")


    failed = service.authenticate(

        "admin@smiledental.com",

        "WrongPassword",

    )


    assert failed is None

    print("✅ Invalid password rejected")


    missing = service.authenticate(

        "unknown@demo.com",

        "SecurePass123!",

    )


    assert missing is None

    print("✅ Unknown user rejected")


    stored = service.get_user(

        "admin@smiledental.com",

    )


    assert stored is not None

    print("✅ User lookup successful")


    assert service.logout(

        "admin@smiledental.com",

    )

    print("✅ Logout successful")


    assert (

        service.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 AUTHENTICATION SERVICE TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()