from heshly_core.models.tenant_configuration import (
    TenantConfiguration,
)

from heshly_core.repositories.configuration_repository import (
    ConfigurationRepository,
)


def run_test():

    print("\n===================================")
    print("Configuration Repository Test")
    print("===================================\n")

    repository = ConfigurationRepository()

    configuration = TenantConfiguration(

        tenant_id="tenant_001",

    )

    configuration.set(

        "timezone",

        "Africa/Nairobi",

    )

    repository.save(
        configuration
    )

    print("✅ Configuration saved")

    stored = repository.get(
        "tenant_001"
    )

    assert stored is not None

    print("✅ Configuration retrieved")

    assert stored.get(
        "timezone"
    ) == "Africa/Nairobi"

    print("✅ Configuration value verified")

    assert repository.exists(
        "tenant_001"
    )

    print("✅ Exists check passed")

    assert repository.count() == 1

    print("✅ Count passed")

    repository.delete(
        "tenant_001"
    )

    assert repository.count() == 0

    print("✅ Delete passed")

    print(
        "\n🎉 CONFIGURATION REPOSITORY TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()