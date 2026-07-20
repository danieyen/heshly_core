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

from heshly_core.services.auth.api_permissions import (
    APIPermissions,
)


@dataclass(slots=True)
class Workflow:

    tenant_id: str

    name: str


@dataclass(slots=True)
class AIProfile:

    tenant_id: str

    personality: str


def run_test():

    print("\n================================")
    print("Full SaaS Integration Test")
    print("================================\n")


    context = TenantContextManager()

    permissions = APIPermissions()

    filter_service = RepositoryTenantFilter()


    tenant = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

    )


    context.set(
        tenant
    )

    print("✅ Tenant context established")


    permissions.assign(

        "admin001",

        [

            "tenant.view",

            "appointment.manage",

            "crm.manage",

        ],

    )


    assert permissions.check(

        "admin001",

        "appointment.manage",

    )

    print("✅ Permission verified")


    workflows = [

        Workflow(

            tenant_id="tenant001",

            name="Appointment Booking",

        ),

        Workflow(

            tenant_id="tenant002",

            name="Lead Qualification",

        ),

    ]


    available_workflows = (

        filter_service.filter(
            workflows
        )

    )


    assert len(
        available_workflows
    ) == 1

    assert (

        available_workflows[0].name

        ==

        "Appointment Booking"

    )

    print("✅ Workflow isolation verified")


    profiles = [

        AIProfile(

            tenant_id="tenant001",

            personality="Professional",

        ),

        AIProfile(

            tenant_id="tenant002",

            personality="Friendly",

        ),

    ]


    active_profile = (

        filter_service.filter(
            profiles
        )

    )


    assert len(
        active_profile
    ) == 1

    assert (

        active_profile[0].personality

        ==

        "Professional"

    )

    print("✅ AI customization verified")


    context.clear()

    assert context.get() is None

    print("✅ Tenant context cleared")


    print(
        "\n🎉 FULL SAAS INTEGRATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()