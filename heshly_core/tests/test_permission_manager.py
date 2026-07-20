from heshly_core.models.role import (
    Permission,
    Role,
    RoleType,
)

from heshly_core.services.security.permission_manager import (
    PermissionManager,
)


def run_test():

    print("\n==============================")
    print("Permission Manager Test")
    print("==============================\n")

    manager = PermissionManager()

    role = Role(
        role_id="owner",
        name="Owner",
        role_type=RoleType.OWNER,
    )

    permission = Permission(
        permission_id="perm_001",
        resource="appointments",
        action="create",
    )

    manager.grant(
        role,
        permission,
    )

    assert manager.has_permission(
        role,
        "appointments",
        "create",
    )

    print("✅ Permission grant passed")

    assert not manager.has_permission(
        role,
        "billing",
        "delete",
    )

    print("✅ Permission validation passed")

    assert manager.revoke(
        role,
        "appointments",
        "create",
    )

    print("✅ Permission revoke passed")

    assert not manager.has_permission(
        role,
        "appointments",
        "create",
    )

    print("✅ Permission removal passed")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 PERMISSION MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()