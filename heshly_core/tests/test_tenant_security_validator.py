from dataclasses import dataclass

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.tenant.tenant_security_validator import (
    TenantSecurityValidator,
)


@dataclass(slots=True)
class Resource:

    resource_id: str

    tenant_id: str


def run_test():

    print("\n==============================")
    print("Tenant Security Validator Test")
    print("==============================\n")

    context = TenantContext()

    tenant = Tenant(

        tenant_id="tenant_001",

        name="Demo Tenant",

    )

    context.set(
        tenant
    )

    validator = TenantSecurityValidator()

    assert validator.validate_context()

    print("✅ Context validation passed")

    resource = Resource(

        resource_id="resource_001",

        tenant_id="tenant_001",

    )

    assert validator.validate_resource(
        resource
    )

    print("✅ Resource validation passed")

    query = {

        "tenant_id": "tenant_001",

        "status": "active",

    }

    assert validator.validate_query(
        query
    )

    print("✅ Query validation passed")

    assert validator.validate(

        resource=resource,

        query=query,

    )

    print("✅ Full validation passed")

    assert (

        validator.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check passed")

    context.clear()

    print(
        "\n🎉 TENANT SECURITY VALIDATOR TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()