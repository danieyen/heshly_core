from heshly_core.models.role import (
    Permission,
    PermissionAction,
    PermissionCategory,
    Role,
    RoleType,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)
from heshly_core.services.auth.custom_roles import (
    CustomRoles,
)


def run_test():

    print("\n================================")
    print("Custom Roles Test")
    print("================================\n")


    repository = RoleRepository()

    service = CustomRoles(repository)


    role = Role(

        role_id="role001",

        name="Front Desk",

        role_type=RoleType.CUSTOM,

        tenant_id="tenant001",

    )


    service.create(role)

    print("✅ Custom role created")


    permission = Permission(

        permission_id="perm001",

        resource="appointment",

        action=PermissionAction.CREATE,

        category=PermissionCategory.APPOINTMENTS,

    )


    assert service.add_permission(

        "role001",

        permission,

    )

    print("✅ Permission added")


    assert repository.get(

        "role001"

    ).permission_count == 1

    print("✅ Permission count verified")


    copied = service.copy(

        source_role=role,

        role_id="role002",

        name="Reception",

    )

    assert copied.role_id == "role002"

    print("✅ Role copied")


    renamed = service.rename(

        "role002",

        "Reception Lead",

    )

    assert renamed is not None

    assert renamed.name == "Reception Lead"

    print("✅ Role renamed")


    assert service.remove_permission(

        "role001",

        "appointment",

        PermissionAction.CREATE,

    )

    print("✅ Permission removed")


    assert service.delete(
        "role002"
    )

    print("✅ Role deleted")


    assert (

        service.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 CUSTOM ROLES TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()