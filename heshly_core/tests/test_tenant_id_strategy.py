from heshly_core.services.tenant.tenant_id_strategy import (
    TenantIDStrategy,
)


def run_test():

    print("\n==============================")
    print("Tenant ID Strategy Test")
    print("==============================\n")

    tenant_id = TenantIDStrategy.generate()

    assert TenantIDStrategy.is_valid(
        tenant_id
    )

    print("✅ Tenant ID generation passed")

    normalized = TenantIDStrategy.normalize(
        "  TENANT_ABC123  "
    )

    assert normalized == "tenant_abc123"

    print("✅ Normalization passed")

    summary = TenantIDStrategy.summary()

    assert summary["prefix"] == "tenant"

    print("✅ Summary passed")

    health = TenantIDStrategy.health()

    assert health["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 TENANT ID STRATEGY TEST PASSED\n")


if __name__ == "__main__":

    run_test()