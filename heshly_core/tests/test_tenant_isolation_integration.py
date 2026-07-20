from dataclasses import dataclass

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)

from heshly_core.services.tenant.repository_tenant_filter import (
    RepositoryTenantFilter,
)

from heshly_core.services.tenant.query_isolation import (
    QueryIsolation,
)

from heshly_core.services.tenant.cross_tenant_access import (
    CrossTenantAccess,
)

from heshly_core.services.tenant.tenant_security_validator import (
    TenantSecurityValidator,
)


@dataclass(slots=True)
class Resource:

    resource_id: str

    tenant_id: str


def run_test():

    print("\n===================================")
    print("Tenant Isolation Integration Test")
    print("===================================\n")

    context = TenantContextManager()

    tenant = Tenant(

        tenant_id="tenant_001",

        name="Demo Tenant",

    )

    context.set(
        tenant
    )

    # ==========================================
    # Repository Filter
    # ==========================================

    resources = [

        Resource(
            "1",
            "tenant_001",
        ),

        Resource(
            "2",
            "tenant_001",
        ),

        Resource(
            "3",
            "tenant_002",
        ),

    ]

    repository_filter = RepositoryTenantFilter()

    filtered = repository_filter.filter(
        resources
    )

    assert len(filtered) == 2

    print("✅ Repository filtering passed")

    # ==========================================
    # Query Isolation
    # ==========================================

    query = QueryIsolation().apply(

        {

            "status": "active",

        }

    )

    assert (

        query["tenant_id"]

        ==

        "tenant_001"

    )

    print("✅ Query isolation passed")

    # ==========================================
    # Cross-Tenant Access
    # ==========================================

    access = CrossTenantAccess()

    assert access.authorize(
        filtered[0]
    )

    print("✅ Same-tenant access passed")

    try:

        access.authorize(
            Resource(
                "4",
                "tenant_999",
            )
        )

        raise AssertionError(
            "Cross-tenant access should fail."
        )

    except PermissionError:

        print("✅ Cross-tenant access blocked")

    # ==========================================
    # Validator
    # ==========================================

    validator = TenantSecurityValidator()

    assert validator.validate(

        resource=filtered[0],

        query=query,

    )

    print("✅ Security validation passed")

    context.clear()

    print(
        "\n🎉 TENANT ISOLATION INTEGRATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()