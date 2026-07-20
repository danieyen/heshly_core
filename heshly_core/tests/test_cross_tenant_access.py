from dataclasses import dataclass

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)

from heshly_core.services.tenant.cross_tenant_access import (
    CrossTenantAccess,
)


@dataclass(slots=True)
class Resource:

    resource_id: str

    tenant_id: str


def run_test():

    print("\n==============================")
    print("Cross-Tenant Access Test")
    print("==============================\n")

    context = TenantContextManager()

    tenant = Tenant(

        tenant_id="tenant_001",

        name="Demo Tenant",

    )

    context.set(
        tenant
    )

    access = CrossTenantAccess()

    own_resource = Resource(

        resource_id="res_001",

        tenant_id="tenant_001",

    )

    assert access.authorize(
        own_resource
    )

    print("✅ Own resource access passed")

    other_resource = Resource(

        resource_id="res_002",

        tenant_id="tenant_002",

    )

    try:

        access.authorize(
            other_resource
        )

        raise AssertionError(
            "Cross-tenant access should fail."
        )

    except PermissionError:

        print("✅ Cross-tenant access blocked")

    assert not access.can_access(
        other_resource
    )

    print("✅ Access validation passed")

    assert (

        access.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check passed")

    context.clear()

    print(
        "\n🎉 CROSS-TENANT ACCESS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()