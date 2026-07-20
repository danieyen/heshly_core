from heshly_core.models.role import (
    Permission,
    PermissionAction,
    PermissionCategory,
)

from heshly_core.repositories.permission_repository import (
    PermissionRepository,
)


def run_test():

    print("\n================================")
    print("Permission Repository Test")
    print("================================\n")


    repository = PermissionRepository()


    appointment_permission = Permission(

        permission_id="perm001",

        resource="appointment",

        action=PermissionAction.CREATE,

        category=PermissionCategory.APPOINTMENTS,

    )


    crm_permission = Permission(

        permission_id="perm002",

        resource="crm",

        action=PermissionAction.MANAGE,

        category=PermissionCategory.CRM,

    )


    repository.save(
        appointment_permission
    )

    repository.save(
        crm_permission
    )

    print("✅ Permissions saved")


    assert repository.count() == 2

    print("✅ Count verified")


    assert repository.exists(
        "perm001"
    )

    print("✅ Exists verified")


    permission = repository.get(
        "perm001"
    )

    assert permission is not None

    print("✅ Get verified")


    by_key = repository.get_by_key(
        "appointment.create"
    )

    assert by_key is not None

    print("✅ Key lookup verified")


    appointments = repository.list_by_resource(
        "appointment"
    )

    assert len(appointments) == 1

    print("✅ Resource lookup verified")


    crm = repository.list_by_category(
        PermissionCategory.CRM
    )

    assert len(crm) == 1

    print("✅ Category lookup verified")


    repository.delete(
        "perm001"
    )

    assert repository.count() == 1

    print("✅ Delete verified")


    repository.clear()

    assert repository.count() == 0

    print("✅ Clear verified")


    assert repository.health()["status"] == "healthy"

    print("✅ Health check")


    print(
        "\n🎉 PERMISSION REPOSITORY TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()