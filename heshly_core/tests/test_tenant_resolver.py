from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.repositories.tenant_repository import (
    TenantRepository,
)

from heshly_core.services.tenant.tenant_resolver import (
    TenantResolver,
)



def run_test():

    print("\n==============================")
    print("Tenant Resolver Test")
    print("==============================\n")


    resolver = TenantResolver()


    tenant = Tenant(
        tenant_id="tenant_001",
        name="Acme Dental",
        email="admin@acme.com",
        phone="+254700000001",
    )


    resolver.repository.save(
        tenant
    )


    # ----------------------------------
    # Resolve ID
    # ----------------------------------

    result = resolver.resolve_by_id(
        "tenant_001"
    )


    assert result is not None

    assert result.name == "Acme Dental"


    print("✅ Resolve by ID passed")


    # ----------------------------------
    # Resolve Email
    # ----------------------------------

    resolver.clear()


    result = resolver.resolve_by_email(
        "admin@acme.com"
    )


    assert result is not None


    print("✅ Resolve by email passed")


    # ----------------------------------
    # Resolve Phone
    # ----------------------------------

    resolver.clear()


    result = resolver.resolve_by_phone(
        "+254700000001"
    )


    assert result is not None


    print("✅ Resolve by phone passed")


    # ----------------------------------
    # Context
    # ----------------------------------

    current = resolver.current()


    assert current.tenant_id == "tenant_001"


    print("✅ Tenant context populated passed")


    resolver.clear()


    print("✅ Clear context passed")


    print("\n🎉 TENANT RESOLVER TEST PASSED\n")



if __name__ == "__main__":

    run_test()