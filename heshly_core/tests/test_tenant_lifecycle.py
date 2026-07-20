from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)

from heshly_core.services.tenant.tenant_lifecycle import (
    TenantLifecycle,
)



def run_test():

    print("\n==============================")
    print("Tenant Lifecycle Test")
    print("==============================\n")


    lifecycle = TenantLifecycle()


    tenant = Tenant(
        tenant_id="tenant_001",
        name="Acme Dental",
    )


    lifecycle.create_tenant(
        tenant
    )


    assert lifecycle.status(
        "tenant_001"
    ) == TenantStatus.TRIAL


    print("✅ Create tenant passed")


    lifecycle.activate_tenant(
        "tenant_001"
    )


    assert lifecycle.status(
        "tenant_001"
    ) == TenantStatus.ACTIVE


    print("✅ Activate tenant passed")


    lifecycle.suspend_tenant(
        "tenant_001"
    )


    assert lifecycle.status(
        "tenant_001"
    ) == TenantStatus.SUSPENDED


    print("✅ Suspend tenant passed")


    lifecycle.delete_tenant(
        "tenant_001"
    )


    assert lifecycle.status(
        "tenant_001"
    ) == TenantStatus.DELETED


    print("✅ Delete tenant passed")


    print("\n🎉 TENANT LIFECYCLE TEST PASSED\n")



if __name__ == "__main__":

    run_test()