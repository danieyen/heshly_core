from heshly_core.models.crm import Lead
from heshly_core.services.crm.lead_assignment_manager import (
    LeadAssignmentManager,
)


def run():

    manager = LeadAssignmentManager()

    lead = Lead(
        lead_id="LEAD-001",
        business_id="BIZ-001",
        full_name="John Doe",
        phone="+254700123456",
    )


    # Assign

    result = manager.assign(
        lead,
        "Sales Agent 1",
    )

    print(result)

    assert result.success
    assert lead.assigned_to == "Sales Agent 1"


    # Reassign

    result = manager.reassign(
        lead,
        "Sales Agent 2",
    )

    print(result)

    assert lead.assigned_to == "Sales Agent 2"


    # Unassign

    result = manager.unassign(
        lead,
    )

    print(result)

    assert lead.assigned_to is None


    print(
        "\n✅ Lead Assignment Functional Test Passed"
    )


if __name__ == "__main__":
    run()