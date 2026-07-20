from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.auth.session_manager import (
    SessionManager,
)


def run_test():

    print("\n================================")
    print("Session Manager Test")
    print("================================\n")


    manager = SessionManager()


    user = AuthUser(

        user_id="user001",

        tenant_id="tenant001",

        email="admin@smiledental.com",

    )


    session = manager.create_session(
        user
    )


    print("✅ Session created")


    retrieved = manager.get_session(

        session.session_id

    )


    assert retrieved is not None

    print("✅ Session retrieved")


    assert manager.validate(

        session.session_id

    )

    print("✅ Session validated")


    assert manager.active_sessions() == 1

    print("✅ Active session count correct")


    assert manager.destroy_session(

        session.session_id

    )

    print("✅ Session destroyed")


    assert manager.active_sessions() == 0

    print("✅ Session removal verified")


    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 SESSION MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()