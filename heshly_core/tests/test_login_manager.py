from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.authentication_service import (
    AuthenticationService,
)

from heshly_core.services.auth.login_manager import (
    LoginManager,
)


def run_test():

    print("\n================================")
    print("Login Manager Test")
    print("================================\n")


    auth = AuthenticationService()

    login = LoginManager(auth)


    user = AuthUser(

        user_id="user001",

        tenant_id="tenant001",

        email="admin@smiledental.com",

        first_name="John",

        last_name="Doe",

    )


    auth.register(

        user,

        "SecurePass123!",

    )


    print("✅ User registered")


    logged_in = login.login(

        "admin@smiledental.com",

        "SecurePass123!",

    )


    assert logged_in is not None

    print("✅ Login successful")


    assert login.is_authenticated()

    print("✅ Authentication state verified")


    current = login.get_current_user()

    assert current is not None

    assert current.email == (
        "admin@smiledental.com"
    )

    print("✅ Current user retrieved")


    login.logout()

    assert not login.is_authenticated()

    print("✅ Logout successful")


    assert (

        login.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 LOGIN MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()