from heshly_core.models.crm import LeadStatus

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.crm.lead_manager import (
    LeadManager,
)


def run():

    TenantContext().set("heshly")

    manager = LeadManager()


    # Create

    lead = manager.create_lead(
        business_id="heshly",
        full_name="John Doe",
        phone="+254700123456",
        email=f"john-{__import__("uuid").uuid4().hex[:8]}@example.com",
        company="ABC Ltd",
    )

    print("Created:")
    print(lead)


    assert lead.full_name == "John Doe"


    # Assign

    result = manager.assign_lead(
        lead,
        "Sales Agent 1",
    )

    print("\nAssigned:")
    print(result)


    assert lead.assigned_to == "Sales Agent 1"


    # Qualify

    result = manager.qualify_lead(
        lead
    )

    print("\nQualified:")
    print(result)


    assert lead.status == LeadStatus.QUALIFIED


    # Score

    result = manager.score_lead(
        lead
    )

    print("\nScore:")
    print(result)


    assert lead.score > 0


    # Status Update

    result = manager.update_status(
        lead,
        LeadStatus.CONVERTED,
    )

    print("\nConverted:")
    print(result)


    assert lead.status == LeadStatus.CONVERTED


    print(
        "\n✅ Lead Manager Functional Test Passed"
    )


if __name__ == "__main__":
    run()
