from heshly_core.services.auth.system_roles import (
    SystemRoles,
)


def run_test():

    print("\n================================")
    print("System Roles Test")
    print("================================\n")


    roles = SystemRoles.all_roles()

    assert len(roles) == 6

    print("✅ System roles created")


    owner = SystemRoles.tenant_owner()

    assert owner.permission_count > 0

    print("✅ Owner permissions")


    admin = SystemRoles.platform_admin()

    assert admin.can(

        "system",

        "manage",

    )

    print("✅ Platform admin permissions")


    staff = SystemRoles.staff()

    assert staff.can(

        "appointment",

        "create",

    )

    print("✅ Staff permissions")


    print("\n🎉 SYSTEM ROLES TEST PASSED\n")


if __name__ == "__main__":

    run_test()