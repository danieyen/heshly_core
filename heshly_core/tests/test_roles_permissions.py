from heshly_core.models.role import (
    Role,
    Permission,
    RoleType,
)



def run_test():

    print("\n==============================")
    print("Roles & Permissions Test")
    print("==============================\n")



    role = Role(

        role_id="role_owner",

        name="Owner",

        role_type=RoleType.OWNER,

    )


    print("✅ Role creation passed")



    permission = Permission(

        permission_id="perm_001",

        resource="appointments",

        action="create",

        description="Create appointments",

    )


    role.add_permission(
        permission
    )


    assert role.permission_count == 1


    print("✅ Permission assignment passed")



    assert (
        role.can(
            "appointments",
            "create",
        )
    )


    print("✅ Permission validation passed")



    assert not role.can(

        "billing",

        "delete",

    )


    print("✅ Permission denial passed")



    print("\n🎉 ROLES & PERMISSIONS TEST PASSED\n")



if __name__ == "__main__":

    run_test()