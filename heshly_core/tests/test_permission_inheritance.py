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
from heshly_core.services.auth.permission_inheritance import (
    PermissionInheritance,
)


def run_test():

    print("\n================================")
    print("Permission Inheritance Test")
    print("================================\n")

    repository = RoleRepository()

    owner = Role(

        role_id="owner",

        name="Owner",

        role_type=RoleType.OWNER,

    )

    owner.add_permission(

        Permission(

            permission_id="perm001",

            resource="billing",

            action=PermissionAction.MANAGE,

            category=PermissionCategory.BILLING,

        )

    )

    manager = Role(

        role_id="manager",

        name="Manager",

        role_type=RoleType.MANAGER,

    )

    manager.add_permission(

        Permission(

            permission_id="perm002",

            resource="crm",

            action=PermissionAction.MANAGE,

            category=PermissionCategory.CRM,

        )

    )

    receptionist = Role(

        role_id="reception",

        name="Receptionist",

        role_type=RoleType.STAFF,

    )

    receptionist.add_permission(

        Permission(

            permission_id="perm003",

            resource="appointment",

            action=PermissionAction.CREATE,

            category=PermissionCategory.APPOINTMENTS,

        )

    )

    repository.save(owner)
    repository.save(manager)
    repository.save(receptionist)

    inheritance = PermissionInheritance(
        repository
    )

    inheritance.inherit(
        "manager",
        "owner",
    )

    inheritance.inherit(
        "reception",
        "manager",
    )

    print("✅ Inheritance configured")

    assert inheritance.has_permission(
        "reception",
        "appointment",
        PermissionAction.CREATE,
    )

    print("✅ Own permission inherited")

    assert inheritance.has_permission(
        "reception",
        "crm",
        PermissionAction.MANAGE,
    )

    print("✅ Manager permission inherited")

    assert inheritance.has_permission(
        "reception",
        "billing",
        PermissionAction.MANAGE,
    )

    print("✅ Owner permission inherited")

    permissions = inheritance.permissions(
        "reception"
    )

    assert len(permissions) == 3

    print("✅ Effective permissions resolved")

    assert (
        inheritance.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check")

    print(
        "\n🎉 PERMISSION INHERITANCE TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()