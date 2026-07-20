from heshly_core.services.configuration.configuration_manager import (
    ConfigurationManager,
)


def run_test():

    print("\n================================")
    print("Configuration Manager Test")
    print("================================\n")

    manager = ConfigurationManager()

    manager.set(

        tenant_id="tenant_001",

        key="timezone",

        value="Africa/Nairobi",

    )

    print("✅ Configuration stored")

    value = manager.value(

        "tenant_001",

        "timezone",

    )

    assert value == "Africa/Nairobi"

    print("✅ Configuration retrieved")

    assert manager.exists(
        "tenant_001"
    )

    print("✅ Exists check passed")

    configuration = manager.get(
        "tenant_001"
    )

    assert configuration is not None

    print("✅ Configuration object retrieved")

    assert manager.remove(

        "tenant_001",

        "timezone",

    )

    print("✅ Configuration removed")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 CONFIGURATION MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()