from heshly_core.models.platform_admin import (
    PlatformAdmin,
    PlatformAdminRole,
)


def run_test():

    print("\n==============================")
    print("Platform Admin Model Test")
    print("==============================\n")

    admin = PlatformAdmin(

        admin_id="admin001",

        first_name="Dan",

        last_name="Mwathi",

        email="admin@heshly.com",

        role=PlatformAdminRole.SUPER_ADMIN,

    )

    assert admin.active

    print("✅ Admin created")

    admin.verify()

    assert admin.verified

    print("✅ Verification")

    admin.suspend()

    assert not admin.active

    print("✅ Suspension")

    admin.activate()

    assert admin.active

    print("✅ Activation")

    assert admin.full_name == "Dan Mwathi"

    print("✅ Full name")

    print("\n🎉 PLATFORM ADMIN MODEL TEST PASSED\n")


if __name__ == "__main__":

    run_test()