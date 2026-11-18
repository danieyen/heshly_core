from dataclasses import dataclass

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.tenant.repository_tenant_filter import (
    RepositoryTenantFilter,
)


@dataclass(slots=True)
class Record:

    record_id: str

    tenant_id: str


def run_test():

    print("\n==============================")
    print("Repository Tenant Filter Test")
    print("==============================\n")

    context = TenantContext()

    tenant = Tenant(

        tenant_id="tenant_001",

        name="Demo Tenant",

    )

    context.set(
        tenant
    )

    records = [

        Record(
            "1",
            "tenant_001",
        ),

        Record(
            "2",
            "tenant_001",
        ),

        Record(
            "3",
            "tenant_002",
        ),

    ]

    tenant_filter = RepositoryTenantFilter()

    filtered = tenant_filter.filter(
        records
    )

    assert len(filtered) == 2

    print("✅ Tenant filtering passed")

    assert tenant_filter.validate(
        filtered[0]
    )

    print("✅ Record validation passed")

    health = tenant_filter.health()

    assert health["status"] == "healthy"

    print("✅ Health check passed")

    context.clear()

    print("\n🎉 REPOSITORY TENANT FILTER TEST PASSED\n")


if __name__ == "__main__":

    run_test()

    if __name__ == "__main__":
        run_test()