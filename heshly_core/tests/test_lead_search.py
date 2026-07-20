from heshly_core.models.crm import (
    Lead,
    LeadStatus,
)

from heshly_core.services.crm.lead_search_engine import (
    LeadSearchEngine,
)


def run():

    engine = LeadSearchEngine()


    leads = [

        Lead(
            lead_id="LEAD-001",
            business_id="BIZ-001",
            full_name="John Doe",
            phone="+254700111111",
            email="john@example.com",
            status=LeadStatus.QUALIFIED,
            score=80,
            assigned_to="Agent 1",
        ),


        Lead(
            lead_id="LEAD-002",
            business_id="BIZ-001",
            full_name="Jane Smith",
            phone="+254700222222",
            status=LeadStatus.NEW,
            score=20,
            assigned_to="Agent 2",
        ),


        Lead(
            lead_id="LEAD-003",
            business_id="BIZ-001",
            full_name="Peter Kamau",
            email="peter@example.com",
            status=LeadStatus.CONTACTED,
            score=50,
            assigned_to="Agent 1",
        ),

    ]


    # Search name

    result = engine.search(
        leads,
        query="John",
    )

    print("Name Search:")
    print(result)

    assert len(result) == 1


    # Search status

    result = engine.search(
        leads,
        status=LeadStatus.QUALIFIED,
    )

    print("\nStatus Search:")
    print(result)

    assert len(result) == 1


    # Search assigned agent

    result = engine.search(
        leads,
        assigned_to="Agent 1",
    )

    print("\nAgent Search:")
    print(result)

    assert len(result) == 2


    # Search score

    result = engine.search(
        leads,
        min_score=70,
    )

    print("\nScore Search:")
    print(result)

    assert len(result) == 1


    print(
        "\n✅ Lead Search Functional Test Passed"
    )


if __name__ == "__main__":
    run()