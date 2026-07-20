from heshly_core.models.session import (
    UserSession,
    SessionStatus,
)


def run_test():

    print("\n================================")
    print("Session Model Test")
    print("================================\n")

    session = UserSession(

        user_id="user001",

        tenant_id="tenant001",

        access_token="access-token",

        refresh_token="refresh-token",

        ip_address="192.168.1.10",

        user_agent="Chrome",

    )

    assert session.is_active

    print("✅ Active session")

    session.touch()

    print("✅ Activity updated")

    session.extend()

    assert session.is_active

    print("✅ Session extended")

    session.revoke()

    assert session.is_revoked

    print("✅ Session revoked")

    data = session.to_dict()

    assert data["user_id"] == "user001"

    print("✅ Serialization")

    assert session.status == SessionStatus.REVOKED

    print("✅ Status verified")

    print(
        "\n🎉 SESSION MODEL TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()