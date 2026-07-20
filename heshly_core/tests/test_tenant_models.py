from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
    TenantConfiguration,
    TenantMetadata,
)


def run_test():

    print("\n==============================")
    print("Tenant Models Test")
    print("==============================\n")


    tenant = Tenant(
        tenant_id="tenant_001",
        name="Acme Dental Clinic",
        email="admin@acme.com",
        configuration=TenantConfiguration(
            industry="Dental"
        ),
        metadata=TenantMetadata(
            source="signup"
        ),
    )


    assert tenant.tenant_id == "tenant_001"

    assert tenant.status == TenantStatus.TRIAL


    print("✅ Tenant creation passed")


    tenant.activate()


    assert tenant.status == TenantStatus.ACTIVE

    assert tenant.is_active


    print("✅ Tenant activation passed")


    tenant.suspend()


    assert tenant.status == TenantStatus.SUSPENDED


    print("✅ Tenant suspension passed")


    tenant.delete()


    assert tenant.status == TenantStatus.DELETED


    print("✅ Tenant deletion passed")


    print("\n🎉 TENANT MODELS TEST PASSED\n")



if __name__ == "__main__":

    run_test()