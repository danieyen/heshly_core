from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.models.auth import (
    AuthUser,
)

from heshly_core.services.tenant.tenant_context_injection import (
    TenantContextInjection,
)


def run_test():

    print("\n================================")
    print("Tenant Context Injection Test")
    print("================================\n")


    service = TenantContextInjection()


    tenant = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

    )


    user = AuthUser(

        user_id="user001",

        email="admin@smile.com",

        tenant_id="tenant001",

    )


    service.inject(

        user,

        tenant,

    )


    print("✅ Tenant injected")


    current = service.current()


    assert current is not None


    assert (
        current.tenant_id
        ==
        "tenant001"
    )


    print("✅ Tenant context available")


    service.clear()


    assert (
        service.current()
        is None
    )


    print("✅ Context cleared")


    assert (
        service.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health check")


    print(
        "\n🎉 TENANT CONTEXT INJECTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()