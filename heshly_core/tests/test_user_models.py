from heshly_core.models.user import (
    User,
    UserRole,
    UserStatus,
)



def run_test():

    print("\n==============================")
    print("User Model Test")
    print("==============================\n")



    user = User(

        user_id="user_001",

        tenant_id="tenant_001",

        name="Dr. Kamau",

        email="kamau@acme.com",

        phone="+254700000001",

        role=UserRole.OWNER,

    )



    assert user.user_id == "user_001"


    print("✅ User creation passed")



    assert user.tenant_id == "tenant_001"


    print("✅ Tenant ownership passed")



    assert user.role == UserRole.OWNER


    print("✅ Role assignment passed")



    assert user.is_active


    print("✅ Default active status passed")



    user.suspend()


    assert (
        user.status
        ==
        UserStatus.SUSPENDED
    )


    print("✅ Suspension passed")



    user.activate()


    assert user.is_active


    print("✅ Activation passed")



    user.deactivate()


    assert (
        user.status
        ==
        UserStatus.INACTIVE
    )


    print("✅ Deactivation passed")



    assert user.has_role(
        UserRole.OWNER
    )


    print("✅ Role check passed")



    print("\n🎉 USER MODEL TEST PASSED\n")



if __name__ == "__main__":

    run_test()