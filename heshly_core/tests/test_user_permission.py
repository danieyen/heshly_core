from heshly_core.services.auth.api_permissions import (
    APIPermissions,
)


def run_test():

    print("\n================================")
    print("User Permission Test")
    print("================================\n")


    permissions = APIPermissions()


    # ==========================================
    # Create Admin User
    # ==========================================

    permissions.assign(

        "admin001",

        [

            "tenant.view",

            "tenant.manage",

            "billing.manage",

        ]

    )


    print(
        "✅ Admin permissions assigned"
    )


    # ==========================================
    # Create Staff User
    # ==========================================

    permissions.assign(

        "staff001",

        [

            "appointment.view",

            "appointment.create",

        ]

    )


    print(
        "✅ Staff permissions assigned"
    )


    # ==========================================
    # Admin Access
    # ==========================================

    assert permissions.check(

        "admin001",

        "tenant.manage",

    )


    print(
        "✅ Admin permission allowed"
    )


    # ==========================================
    # Staff Allowed Action
    # ==========================================

    assert permissions.check(

        "staff001",

        "appointment.view",

    )


    print(
        "✅ Staff permission allowed"
    )


    # ==========================================
    # Staff Restricted Action
    # ==========================================

    assert not permissions.check(

        "staff001",

        "billing.manage",

    )


    print(
        "✅ Restricted permission blocked"
    )


    # ==========================================
    # Unknown User
    # ==========================================

    assert not permissions.check(

        "unknown001",

        "tenant.view",

    )


    print(
        "✅ Unknown user blocked"
    )


    # ==========================================
    # Require Permission
    # ==========================================

    try:

        permissions.require(

            "staff001",

            "tenant.manage",

        )

        assert False


    except PermissionError:

        print(
            "✅ Permission exception raised"
        )


    # ==========================================
    # Health
    # ==========================================

    assert (

        permissions.health()["status"]

        ==

        "healthy"

    )


    print(
        "✅ Health check"
    )


    print(
        "\n🎉 USER PERMISSION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()