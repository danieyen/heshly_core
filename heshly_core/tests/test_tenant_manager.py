from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)

from heshly_core.services.tenant.tenant_manager import (
    TenantManager,
)


def run_test():

    print("\n==============================")
    print("Tenant Manager Test")
    print("==============================\n")


    manager = TenantManager()


    tenant = Tenant(
        tenant_id="tenant_001",
        name="Acme Dental",
    )


    manager.create(
        tenant
    )


    result = manager.get(
        "tenant_001"
    )


    assert result is not None


    print("✅ Tenant creation passed")


    manager.activate(
        "tenant_001"
    )


    assert manager.is_active(
        "tenant_001"
    )


    print("✅ Tenant activation passed")


    manager.suspend(
        "tenant_001"
    )


    assert manager.get(
        "tenant_001"
    ).status == TenantStatus.SUSPENDED


    print("✅ Tenant suspension passed")


    manager.delete(
        "tenant_001"
    )


    assert manager.get(
        "tenant_001"
    ).status == TenantStatus.DELETED


    print("✅ Tenant deletion passed")


    health = manager.health()


    assert health["status"] == "healthy"


    print("✅ Health check passed")


    print("\n🎉 TENANT MANAGER TEST PASSED\n")



if __name__ == "__main__":

    run_test()