from heshly_core.models.role import (
    Role,
    RoleType,
)

from heshly_core.repositories.role_repository import (
    RoleRepository,
)


def run_test():

    print("\n================================")
    print("Role Repository Test")
    print("================================\n")


    repository = RoleRepository()


    owner = Role(

        role_id="role001",

        name="Owner",

        role_type=RoleType.OWNER,

    )


    manager = Role(

        role_id="role002",

        name="Manager",

        role_type=RoleType.MANAGER,

    )


    repository.save(
        owner
    )

    repository.save(
        manager
    )

    print("✅ Roles saved")


    assert repository.count() == 2

    print("✅ Count verified")


    assert repository.exists(
        "role001"
    )

    print("✅ Exists verified")


    retrieved = repository.get(
        "role001"
    )

    assert retrieved is not None

    assert retrieved.name == "Owner"

    print("✅ Get verified")


    by_name = repository.get_by_name(
        "Manager"
    )

    assert by_name is not None

    print("✅ Name lookup verified")


    managers = repository.list_by_type(
        RoleType.MANAGER
    )

    assert len(managers) == 1

    print("✅ Type lookup verified")


    repository.delete(
        "role001"
    )

    assert repository.count() == 1

    print("✅ Delete verified")


    repository.clear()

    assert repository.count() == 0

    print("✅ Clear verified")


    assert (

        repository.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")


    print(
        "\n🎉 ROLE REPOSITORY TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()