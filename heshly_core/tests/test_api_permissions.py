from heshly_core.services.auth.api_permissions import (
    APIPermissions,
)


def run_test():

    print("\n================================")
    print("API Permissions Test")
    print("================================\n")


    permissions = APIPermissions()


    permissions.assign(

        "user001",

        [

            "tenant.view",

            "tenant.manage",

        ]

    )


    print("✅ Permissions assigned")


    allowed = permissions.check(

        "user001",

        "tenant.view",

    )


    assert allowed is True


    print("✅ Permission granted")


    denied = permissions.check(

        "user001",

        "billing.manage",

    )


    assert denied is False


    print("✅ Permission denied")


    try:

        permissions.require(

            "user001",

            "billing.manage",

        )

        assert False


    except PermissionError:

        print(
            "✅ Unauthorized blocked"
        )


    assert (
        permissions.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health check")


    print(
        "\n🎉 API PERMISSIONS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()