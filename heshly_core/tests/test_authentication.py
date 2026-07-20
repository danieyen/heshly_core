from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.authentication_service import (
    AuthenticationService,
)

from heshly_core.services.auth.login_manager import (
    LoginManager,
)

from heshly_core.services.auth.session_manager import (
    SessionManager,
)


def run_test():

    print("\n================================")
    print("Authentication Integration Test")
    print("================================\n")


    # =====================================================
    # Setup
    # =====================================================

    auth_service = AuthenticationService()

    login_manager = LoginManager(
        auth_service
    )

    session_manager = SessionManager()


    # =====================================================
    # Create User
    # =====================================================

    user = AuthUser(

        user_id="user001",

        tenant_id="tenant001",

        email="admin@smiledental.com",

        first_name="John",

        last_name="Doe",

    )


    auth_service.register(

        user,

        "SecurePass123!",

    )


    print("✅ User registered")


    # =====================================================
    # Authenticate
    # =====================================================

    authenticated = login_manager.login(

        "admin@smiledental.com",

        "SecurePass123!",

    )


    assert authenticated is not None

    print("✅ Login successful")


    # =====================================================
    # Session
    # =====================================================

    session = session_manager.create_session(
        authenticated
    )


    assert session is not None

    print("✅ Session created")


    assert session_manager.validate(

        session.session_id

    )

    print("✅ Session validated")


    # =====================================================
    # Current User
    # =====================================================

    current = login_manager.get_current_user()

    assert current is not None

    assert current.email == (
        "admin@smiledental.com"
    )

    print("✅ Current user available")


    # =====================================================
    # Logout
    # =====================================================

    login_manager.logout()

    session_manager.destroy_session(
        session.session_id
    )


    assert not login_manager.is_authenticated()

    assert session_manager.active_sessions() == 0

    print("✅ Logout successful")


    # =====================================================
    # Health Checks
    # =====================================================

    assert (
        auth_service.health()["status"]
        == "healthy"
    )

    assert (
        login_manager.health()["status"]
        == "healthy"
    )

    assert (
        session_manager.health()["status"]
        == "healthy"
    )

    print("✅ All services healthy")


    print(
        "\n🎉 AUTHENTICATION INTEGRATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()