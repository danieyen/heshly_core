from heshly_core.models.role import (
    Role,
    RoleType,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)
from heshly_core.services.auth.system_roles import (
    SystemRoles,
)
from heshly_core.services.auth.tenant_roles import (
    TenantRoles,
)


def run_test():

    print("\n================================")
    print("Tenant Roles Test")
    print("================================\n")


    repository = RoleRepository()

    service = TenantRoles(repository)


    custom = Role(

        role_id="role001",

        name="Front Desk",

        role_type=RoleType.CUSTOM,

    )


    service.create_role(

        "tenant001",

        custom,

    )

    print("✅ Custom role created")


    assert custom.tenant_id == "tenant001"


    owner = SystemRoles.tenant_owner()

    cloned = service.clone_system_role(

        tenant_id="tenant001",

        system_role=owner,

        role_id="role002",

        name="Clinic Owner",

    )

    print("✅ System role cloned")


    assert cloned.tenant_id == "tenant001"

    assert not cloned.system_role


    roles = service.list_roles(
        "tenant001"
    )

    assert len(roles) == 2

    print("✅ Tenant roles listed")


    assert service.delete_role(
        "role001"
    )

    print("✅ Custom role deleted")


    assert repository.count() == 1


    assert (

        service.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 TENANT ROLES TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()