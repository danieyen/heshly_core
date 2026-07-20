from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.admin.tenant_administration import (
    TenantAdministration,
)


def run_test():

    print("\n================================")
    print("Tenant Creation Test")
    print("================================\n")


    service = TenantAdministration()


    # ==========================================
    # Create Tenant 1
    # ==========================================

    tenant_a = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

        email="admin@smiledental.com",

    )


    created_a = service.register(
        tenant_a
    )


    assert created_a.tenant_id == (
        "tenant001"
    )


    print(
        "✅ Tenant A created"
    )


    # ==========================================
    # Create Tenant 2
    # ==========================================

    tenant_b = Tenant(

        tenant_id="tenant002",

        name="Elite Salon",

        email="admin@elitesalon.com",

    )


    created_b = service.register(
        tenant_b
    )


    assert created_b.tenant_id == (
        "tenant002"
    )


    print(
        "✅ Tenant B created"
    )


    # ==========================================
    # Retrieve Tenants
    # ==========================================

    retrieved_a = service.get(
        "tenant001"
    )

    retrieved_b = service.get(
        "tenant002"
    )


    assert retrieved_a is not None

    assert retrieved_b is not None


    print(
        "✅ Tenants retrieved"
    )


    # ==========================================
    # Isolation Check
    # ==========================================

    assert (

        retrieved_a.name

        !=

        retrieved_b.name

    )


    assert (

        retrieved_a.tenant_id

        !=

        retrieved_b.tenant_id

    )


    print(
        "✅ Tenant isolation verified"
    )


    # ==========================================
    # Count Check
    # ==========================================

    tenants = service.list()


    assert len(tenants) == 2


    print(
        "✅ Multiple tenants supported"
    )


    print(
        "\n🎉 TENANT CREATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()