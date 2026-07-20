from dataclasses import dataclass


from heshly_core.models.tenant import (
    Tenant,
)


from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)


from heshly_core.services.tenant.tenant_isolation import (
    TenantIsolation,
)



@dataclass
class TestResource:

    tenant_id: str

    name: str



def run_test():

    print("\n==============================")
    print("Tenant Isolation Test")
    print("==============================\n")


    context = TenantContextManager()

    isolation = TenantIsolation()



    tenant_a = Tenant(
        tenant_id="tenant_a",
        name="Acme Dental",
    )


    context.set(
        tenant_a
    )


    resource = TestResource(
        tenant_id="tenant_a",
        name="Dental Customer",
    )


    assert isolation.validate_owner(
        resource
    )


    print("✅ Same tenant access passed")



    foreign_resource = TestResource(
        tenant_id="tenant_b",
        name="Other Business Customer",
    )


    try:

        isolation.validate_owner(
            foreign_resource
        )

        assert False


    except PermissionError:

        pass


    print("✅ Cross tenant blocking passed")



    context.clear()


    try:

        isolation.require_tenant()

        assert False


    except PermissionError:

        pass


    print("✅ Missing tenant context blocked")


    print("\n🎉 TENANT ISOLATION TEST PASSED\n")



if __name__ == "__main__":

    run_test()