from heshly_core.models.role import (
    Permission,
    PermissionAction,
    Role,
    RoleType,
)


def run_test():

    print("\n================================")
    print("Role Model Test")
    print("================================\n")


    role = Role(

        role_id="role001",

        name="Tenant Owner",

        role_type=RoleType.OWNER,

    )


    print("✅ Role created")


    role.add_permission(

        Permission(

            permission_id="perm001",

            resource="appointment",

            action=PermissionAction.CREATE,

        )

    )


    role.add_permission(

        Permission(

            permission_id="perm002",

            resource="crm",

            action=PermissionAction.MANAGE,

        )

    )


    assert role.can(

        "crm",

        PermissionAction.MANAGE,

    )

    print("✅ Permission check")


    assert role.has_permission(

        "appointment.create"

    )

    print("✅ Permission key lookup")


    role.remove_permission(

        "appointment",

        PermissionAction.CREATE,

    )


    assert not role.can(

        "appointment",

        PermissionAction.CREATE,

    )

    print("✅ Permission removed")


    assert role.health()["status"] == "healthy"

    print("✅ Health check")


    print("\n🎉 ROLE MODEL TEST PASSED\n")


if __name__ == "__main__":

    run_test()