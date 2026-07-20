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
    print("Authorization Integration Test")
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

    authorization = AuthorizationManager(

        role_repository,

        permission_repository,

        assignment_repository,

    )

    appointment_create = Permission(

        permission_id="perm001",

        resource="appointment",

        action=PermissionAction.CREATE,

        category=PermissionCategory.APPOINTMENTS,

    )

    appointment_read = Permission(

        permission_id="perm002",

        resource="appointment",

        action=PermissionAction.READ,

        category=PermissionCategory.APPOINTMENTS,

    )

    crm_manage = Permission(

        permission_id="perm003",

        resource="crm",

        action=PermissionAction.MANAGE,

        category=PermissionCategory.CRM,

    )

    permission_repository.save(
        appointment_create
    )

    permission_repository.save(
        appointment_read
    )

    permission_repository.save(
        crm_manage
    )

    owner = Role(

        role_id="role001",

        name="Owner",

        role_type=RoleType.OWNER,

    )

    owner.add_permission(
        appointment_create
    )

    owner.add_permission(
        appointment_read
    )

    owner.add_permission(
        crm_manage
    )

    role_repository.save(
        owner
    )

    user = AuthUser(

        user_id="user001",

        email="owner@demo.com",

        tenant_id="tenant001",

    )

    assignment_manager.assign(

        user_id=user.user_id,

        role_id=owner.role_id,

        tenant_id=user.tenant_id,

    )

    print("✅ Role assigned")

    assert authorization.has_permission(

        user,

        "appointment",

        PermissionAction.CREATE,

    )

    print("✅ Appointment create allowed")

    assert authorization.has_permission(

        user,

        "appointment",

        PermissionAction.READ,

    )

    print("✅ Appointment read allowed")

    assert authorization.has_permission(

        user,

        "crm",

        PermissionAction.MANAGE,

    )

    print("✅ CRM manage allowed")

    assert not authorization.has_permission(

        user,

        "billing",

        PermissionAction.READ,

    )

    print("✅ Unauthorized action denied")

    permissions = authorization.list_permissions(
        user
    )

    assert len(permissions) == 3

    print("✅ Permission listing")

    assert role_repository.count() == 1

    assert permission_repository.count() == 3

    print("✅ Repository validation")

    assert (

        authorization.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 AUTHORIZATION INTEGRATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()