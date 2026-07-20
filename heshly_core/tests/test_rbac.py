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
from heshly_core.services.auth.permission_inheritance import (
    PermissionInheritance,
)
from heshly_core.services.auth.role_assignment_manager import (
    RoleAssignmentManager,
)


def run_test():

    print("\n================================")
    print("RBAC Integration Test")
    print("================================\n")

    role_repository = RoleRepository()

    permission_repository = PermissionRepository()

    assignment_repository = RoleAssignmentRepository()

    assignment_manager = RoleAssignmentManager(
        assignment_repository
    )

    authorization = AuthorizationManager(

        role_repository,

        permission_repository,

        assignment_repository,

    )

    inheritance = PermissionInheritance(
        role_repository
    )

    # --------------------------------------------------
    # Permissions
    # --------------------------------------------------

    billing = Permission(

        permission_id="perm001",

        resource="billing",

        action=PermissionAction.MANAGE,

        category=PermissionCategory.BILLING,

    )

    crm = Permission(

        permission_id="perm002",

        resource="crm",

        action=PermissionAction.MANAGE,

        category=PermissionCategory.CRM,

    )

    appointment = Permission(

        permission_id="perm003",

        resource="appointment",

        action=PermissionAction.CREATE,

        category=PermissionCategory.APPOINTMENTS,

    )

    permission_repository.save(billing)

    permission_repository.save(crm)

    permission_repository.save(appointment)

    print("✅ Permissions created")

    # --------------------------------------------------
    # Roles
    # --------------------------------------------------

    owner = Role(

        role_id="owner",

        name="Owner",

        role_type=RoleType.OWNER,

    )

    owner.add_permission(billing)

    manager = Role(

        role_id="manager",

        name="Manager",

        role_type=RoleType.MANAGER,

    )

    manager.add_permission(crm)

    receptionist = Role(

        role_id="reception",

        name="Receptionist",

        role_type=RoleType.STAFF,

    )

    receptionist.add_permission(appointment)

    role_repository.save(owner)

    role_repository.save(manager)

    role_repository.save(receptionist)

    print("✅ Roles created")

    # --------------------------------------------------
    # Inheritance
    # --------------------------------------------------

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

        "billing",

        PermissionAction.MANAGE,

    )

    print("✅ Permission inheritance works")

    # --------------------------------------------------
    # User
    # --------------------------------------------------

    user = AuthUser(

        user_id="user001",

        email="admin@demo.com",

        tenant_id="tenant001",

    )

    assignment = assignment_manager.assign(

        user_id=user.user_id,

        role_id="reception",

        tenant_id=user.tenant_id,

    )

    print("✅ Role assigned")

    # --------------------------------------------------
    # Authorization
    # --------------------------------------------------

    assert authorization.has_permission(

        user,

        "appointment",

        PermissionAction.CREATE,

    )

    print("✅ Appointment allowed")

    assert not authorization.has_permission(

        user,

        "billing",

        PermissionAction.MANAGE,

    )

    print("✅ Direct authorization isolated")

    assert inheritance.has_permission(

        "reception",

        "billing",

        PermissionAction.MANAGE,

    )

    print("✅ Inherited permission verified")

    # --------------------------------------------------
    # Removal
    # --------------------------------------------------

    assignment_manager.remove(
        assignment.assignment_id
    )

    assert not authorization.has_permission(

        user,

        "appointment",

        PermissionAction.CREATE,

    )

    print("✅ Role removal verified")

    # --------------------------------------------------
    # Repository Checks
    # --------------------------------------------------

    assert role_repository.count() == 3

    assert permission_repository.count() == 3

    assert assignment_repository.count() == 0

    print("✅ Repository integrity")

    # --------------------------------------------------
    # Health
    # --------------------------------------------------

    assert (

        authorization.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print("\n🎉 RBAC TEST PASSED\n")


if __name__ == "__main__":

    run_test()