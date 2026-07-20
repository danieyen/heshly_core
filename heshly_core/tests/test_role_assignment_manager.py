from heshly_core.repositories.role_assignment_repository import (
    RoleAssignmentRepository,
)

from heshly_core.services.auth.role_assignment_manager import (
    RoleAssignmentManager,
)


def run_test():

    print("\n================================")
    print("Role Assignment Test")
    print("================================\n")


    repository = RoleAssignmentRepository()

    manager = RoleAssignmentManager(
        repository
    )


    assignment = manager.assign(

        user_id="user001",

        role_id="role001",

        tenant_id="tenant001",

        assigned_by="admin",

    )


    print("✅ Role assigned")


    roles = manager.user_roles(
        "user001"
    )

    assert len(roles) == 1

    print("✅ User role lookup")


    assert manager.remove(

        assignment.assignment_id

    )

    print("✅ Role assignment removed")


    assert repository.count() == 0

    print("✅ Repository verified")


    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 ROLE ASSIGNMENT TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()