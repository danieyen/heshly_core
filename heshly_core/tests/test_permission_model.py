from heshly_core.models.role import (
    Permission,
    PermissionAction,
    PermissionCategory,
)


def run_test():

    print("\n================================")
    print("Permission Model Test")
    print("================================\n")


    permission = Permission(

        permission_id="perm001",

        resource="appointment",

        action=PermissionAction.CREATE,

        category=PermissionCategory.APPOINTMENTS,

        description="Create appointments",

    )


    assert (
        permission.key
        ==
        "appointment.create"
    )

    print("✅ Permission key")


    assert permission.is_enabled

    print("✅ Permission enabled")


    permission.disable()

    assert not permission.is_enabled

    print("✅ Permission disabled")


    permission.enable()

    assert permission.is_enabled

    print("✅ Permission enabled again")


    assert (
        permission.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check")


    print(
        "\n🎉 PERMISSION MODEL TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()