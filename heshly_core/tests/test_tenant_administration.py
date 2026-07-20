from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)

from heshly_core.services.admin.tenant_administration import (
    TenantAdministration,
)


def run_test():

    print("\n================================")
    print("Tenant Administration Test")
    print("================================\n")

    service = TenantAdministration()

    tenant = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

        email="admin@smiledental.com",

        phone="+254700000000",

    )

    service.register(
        tenant
    )

    print("✅ Tenant registered")

    stored = service.get(
        "tenant001"
    )

    assert stored is not None

    assert stored.name == "Smile Dental"

    print("✅ Tenant retrieved")

    suspended = service.suspend(
        "tenant001"
    )

    assert suspended

    stored = service.get(
        "tenant001"
    )

    assert stored.status == TenantStatus.SUSPENDED

    print("✅ Tenant suspended")

    activated = service.activate(
        "tenant001"
    )

    assert activated

    stored = service.get(
        "tenant001"
    )

    assert stored.status == TenantStatus.ACTIVE

    print("✅ Tenant activated")

    tenants = service.list()

    assert len(tenants) == 1

    print("✅ Tenant listing")

    removed = service.remove(
        "tenant001"
    )

    assert removed

    print("✅ Tenant removed")

    print(
        "\n🎉 TENANT ADMINISTRATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()