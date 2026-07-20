from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.repositories.tenant_repository import (
    TenantRepository,
)


def run_test():

    print("\n==============================")
    print("Tenant Repository Test")
    print("==============================\n")


    repository = TenantRepository()


    tenant = Tenant(
        tenant_id="tenant_001",
        name="Acme Dental",
    )


    repository.save(
        tenant
    )


    result = repository.get(
        "tenant_001"
    )


    assert result is not None

    assert result.name == "Acme Dental"


    print("✅ Save and retrieve passed")


    tenants = repository.all()


    assert len(tenants) == 1


    print("✅ List tenants passed")


    found = repository.find_by_name(
        "Acme"
    )


    assert len(found) == 1


    print("✅ Search passed")


    summary = repository.summary()


    assert summary["total"] == 1


    print("✅ Summary passed")


    deleted = repository.delete(
        "tenant_001"
    )


    assert deleted


    assert repository.count() == 0


    print("✅ Delete passed")


    print("\n🎉 TENANT REPOSITORY TEST PASSED\n")



if __name__ == "__main__":

    run_test()