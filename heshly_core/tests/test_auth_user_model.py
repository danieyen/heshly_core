from heshly_core.models.auth import (
    AuthUser,
    UserRole,
    UserStatus,
)


def run_test():

    print("\n================================")
    print("Auth User Model Test")
    print("================================\n")


    user = AuthUser(

        user_id="user001",

        tenant_id="tenant001",

        email="admin@smiledental.com",

        first_name="John",

        last_name="Doe",

        role=UserRole.TENANT_OWNER,

    )


    assert user.user_id == "user001"

    print("✅ User created")


    assert user.full_name == "John Doe"

    print("✅ Full name generated")


    assert user.is_active

    print("✅ User active")


    user.record_login()

    assert user.last_login is not None

    print("✅ Login recorded")


    user.lock()

    assert user.status == UserStatus.LOCKED

    print("✅ User locked")


    user.activate()

    assert user.status == UserStatus.ACTIVE

    print("✅ User activated")


    assert user.health()["status"] == "healthy"

    print("✅ Health check")


    print("\n🎉 AUTH USER MODEL TEST PASSED\n")


if __name__ == "__main__":

    run_test()