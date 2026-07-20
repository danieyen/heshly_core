from heshly_core.services.configuration.tenant_preferences_manager import (
    TenantPreferencesManager,
)


def run_test():

    print("\n==============================")
    print("Tenant Preferences Test")
    print("==============================\n")

    manager = TenantPreferencesManager()

    manager.update(

        tenant_id="tenant_001",

        language="en",

        timezone="Africa/Nairobi",

        currency="KES",

        theme="dark",

    )

    preferences = manager.get(
        "tenant_001"
    )

    assert preferences is not None

    print("✅ Preferences created")

    assert preferences.language == "en"

    print("✅ Language preference")

    assert (
        preferences.timezone
        ==
        "Africa/Nairobi"
    )

    print("✅ Timezone preference")

    assert preferences.currency == "KES"

    print("✅ Currency preference")

    assert preferences.theme == "dark"

    print("✅ Theme preference")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 TENANT PREFERENCES TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()