from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)



def run_test():

    print("\n==============================")
    print("Tenant Context Test")
    print("==============================\n")


    context = TenantContext()


    tenant = Tenant(
        tenant_id="tenant_001",
        name="Acme Dental",
    )


    context.set(
        tenant
    )


    current = context.get()


    assert current is not None

    assert current.name == "Acme Dental"


    print("✅ Set and get tenant passed")


    tenant_id = context.tenant_id()


    assert tenant_id == "tenant_001"


    print("✅ Tenant ID retrieval passed")


    assert context.has_context()


    print("✅ Context existence passed")


    required = context.require()


    assert required.tenant_id == "tenant_001"


    print("✅ Required tenant passed")


    context.clear()


    assert not context.has_context()


    print("✅ Context clear passed")


    print("\n🎉 TENANT CONTEXT TEST PASSED\n")



if __name__ == "__main__":

    run_test()