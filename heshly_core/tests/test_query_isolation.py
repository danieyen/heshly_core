from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)

from heshly_core.services.tenant.query_isolation import (
    QueryIsolation,
)


def run_test():

    print("\n==============================")
    print("Query Isolation Test")
    print("==============================\n")

    context = TenantContextManager()

    tenant = Tenant(

        tenant_id="tenant_001",

        name="Demo Tenant",

    )

    context.set(
        tenant
    )

    isolation = QueryIsolation()

    query = isolation.apply(

        {

            "status": "active",

        }

    )

    assert (

        query["tenant_id"]

        ==

        "tenant_001"

    )

    print("✅ Tenant filter applied")

    assert isolation.validate(
        query
    )

    print("✅ Query validation passed")

    assert (
        query["status"]
        ==
        "active"
    )

    print("✅ Existing filters preserved")

    assert (

        isolation.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check passed")

    context.clear()

    print("\n🎉 QUERY ISOLATION TEST PASSED\n")


if __name__ == "__main__":

    run_test()