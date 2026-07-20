from heshly_core.models.auth import AuthUser
from heshly_core.models.role import (
    Permission,
    PermissionAction,
    PermissionCategory,
    Role,
    RoleType,
)
from heshly_core.repositories.permission_repository import (
    PermissionRepository,
)
from heshly_core.repositories.role_assignment_repository import (
    RoleAssignmentRepository,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)
from heshly_core.services.auth.authorization_manager import (
    AuthorizationManager,
)
from heshly_core.services.auth.role_assignment_manager import (
    RoleAssignmentManager,
)


def run_test():

    print("\n================================")
    print("Authorization Manager Test")
    print("================================\n")

    role_repository = RoleRepository()

    permission_repository = PermissionRepository()

    assignment_repository = (
        RoleAssignmentRepository()
    )

    assignment_manager = (
        RoleAssignmentManager(
            assignment_repository
        )
    )

    manager = AuthorizationManager(

        role_repository,

        permission_repository,

        assignment_repository,

    )

    permission = Permission(

        permission_id="perm001",

        resource="appointment",

        action=PermissionAction.CREATE,

        category=PermissionCategory.APPOINTMENTS,

    )

    permission_repository.save(
        permission
    )

    role = Role(

        role_id="role001",

        name="Owner",

        role_type=RoleType.OWNER,

    )

    role.add_permission(
        permission
    )

    role_repository.save(
        role
    )

    user = AuthUser(

        user_id="user001",

        email="admin@demo.com",

        tenant_id="tenant001",

    )

    assignment_manager.assign(

        user_id=user.user_id,

        role_id=role.role_id,

        tenant_id=user.tenant_id,

    )

    print("✅ Role assigned")

    assert manager.has_permission(

        user,

        "appointment",

        PermissionAction.CREATE,

    )

    print("✅ Authorization granted")

    permissions = manager.list_permissions(
        user
    )

    assert len(permissions) == 1

    print("✅ Permission listing verified")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 AUTHORIZATION MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()