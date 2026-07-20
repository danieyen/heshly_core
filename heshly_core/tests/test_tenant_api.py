from heshly_core.api.tenant_api import (
    TenantAPI,
)

from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)


def run_test():

    print("\n================================")
    print("Tenant API Test")
    print("================================\n")


    api = TenantAPI()


    tenant = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

        email="admin@smile.com",

    )


    created = api.create(
        tenant
    )


    assert created.name == "Smile Dental"

    print("✅ Tenant creation")


    stored = api.get(
        "tenant001"
    )


    assert stored is not None

    print("✅ Tenant retrieval")


    assert len(
        api.list()
    ) == 1


    print("✅ Tenant listing")


    api.suspend(
        "tenant001"
    )


    assert (
        api.get(
            "tenant001"
        ).status
        ==
        TenantStatus.SUSPENDED
    )


    print("✅ Tenant suspension")


    api.activate(
        "tenant001"
    )


    assert (
        api.get(
            "tenant001"
        ).status
        ==
        TenantStatus.ACTIVE
    )


    print("✅ Tenant activation")


    assert (
        api.health()["status"]
        ==
        "healthy"
    )


    print("✅ API health")


    print(
        "\n🎉 TENANT API TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()