from heshly_core.models.tenant_configuration import (
    TenantConfiguration,
)


def run_test():

    print("\n================================")
    print("Tenant Configuration Models Test")
    print("================================\n")

    config = TenantConfiguration(

        tenant_id="tenant_001",

    )

    config.set(

        "timezone",

        "Africa/Nairobi",

        "Business timezone",

    )

    assert config.exists(
        "timezone"
    )

    print("✅ Configuration creation passed")

    assert (

        config.get("timezone")

        ==

        "Africa/Nairobi"

    )

    print("✅ Configuration retrieval passed")

    assert config.count == 1

    print("✅ Configuration count passed")

    assert config.remove(
        "timezone"
    )

    print("✅ Configuration removal passed")

    assert config.count == 0

    print("✅ Configuration cleanup passed")

    print(
        "\n🎉 TENANT CONFIGURATION MODELS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()