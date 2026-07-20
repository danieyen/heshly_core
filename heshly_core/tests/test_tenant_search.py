from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)

from heshly_core.services.admin.tenant_search import (
    TenantSearch,
)


def run_test():

    print("\n================================")
    print("Tenant Search Test")
    print("================================\n")


    search = TenantSearch()


    tenant1 = Tenant(

        tenant_id="tenant001",

        name="Smile Dental Clinic",

        email="admin@smiledental.com",

        phone="+254700111111",

    )


    tenant2 = Tenant(

        tenant_id="tenant002",

        name="Nairobi Logistics",

        email="info@nlogistics.com",

        phone="+254700222222",

    )


    search.repository.save(
        tenant1
    )

    search.repository.save(
        tenant2
    )


    print("✅ Tenants created")


    results = search.search(
        "Smile"
    )


    assert len(results) == 1

    assert (
        results[0].name
        ==
        "Smile Dental Clinic"
    )


    print("✅ Name search")


    results = search.search(
        "nlogistics"
    )


    assert len(results) == 1


    print("✅ Email search")


    tenant1.suspend()


    suspended = search.filter_by_status(
        TenantStatus.SUSPENDED
    )


    assert len(suspended) == 1


    print("✅ Status filtering")


    assert (
        search.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health check")


    print(
        "\n🎉 TENANT SEARCH TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()