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
class WorkflowRecord:

    workflow_id: str

    tenant_id: str

    name: str

    version: int = 1


def run_test():

    print("\n================================")
    print("Workflow Separation Test")
    print("================================\n")


    context = TenantContext()

    filter_service = RepositoryTenantFilter()


    tenant_a = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

    )


    tenant_b = Tenant(

        tenant_id="tenant002",

        name="Elite Salon",

    )


    workflows = [

        WorkflowRecord(

            workflow_id="wf001",

            tenant_id="tenant001",

            name="Appointment Booking",

        ),

        WorkflowRecord(

            workflow_id="wf002",

            tenant_id="tenant002",

            name="Lead Qualification",

        ),

    ]


    print("✅ Workflow records created")


    # ==========================================
    # Tenant A
    # ==========================================

    context.set(
        tenant_a
    )


    tenant_a_workflows = filter_service.filter(
        workflows
    )


    assert len(
        tenant_a_workflows
    ) == 1

    assert (
        tenant_a_workflows[0].name
        ==
        "Appointment Booking"
    )


    print("✅ Tenant A workflow isolated")


    # ==========================================
    # Tenant B
    # ==========================================

    context.set(
        tenant_b
    )


    tenant_b_workflows = filter_service.filter(
        workflows
    )


    assert len(
        tenant_b_workflows
    ) == 1

    assert (
        tenant_b_workflows[0].name
        ==
        "Lead Qualification"
    )


    print("✅ Tenant B workflow isolated")


    # ==========================================
    # Cross-Tenant Protection
    # ==========================================

    assert (

        tenant_a_workflows[0].workflow_id

        !=

        tenant_b_workflows[0].workflow_id

    )


    print("✅ Cross-tenant workflow access prevented")


    context.clear()

    assert context.get() is None


    print("✅ Context cleared")


    print(
        "\n🎉 WORKFLOW SEPARATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()