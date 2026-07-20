from heshly_core.models.crm import LeadStatus

from heshly_core.services.crm.lead_manager import (
    LeadManager,
)


def run():

    print("=== Heshly CRM Lead Management Test ===\n")

    manager = LeadManager()


    # =====================================
    # 1. CREATE LEAD
    # =====================================

    lead = manager.create_lead(
        business_id="BIZ-001",
        full_name="Mary Wanjiku",
        phone="+254711222333",
        email="mary@example.com",
        company="Wanjiku Dental Clinic",
        source="whatsapp",
    )

    print("1. Lead Created")
    print(lead)

    assert lead.full_name == "Mary Wanjiku"
    assert lead.status == LeadStatus.NEW


    # =====================================
    # 2. ASSIGN LEAD
    # =====================================

    assignment = manager.assign_lead(
        lead,
        "Sales Agent 1",
    )

    print("\n2. Lead Assigned")
    print(assignment)

    assert lead.assigned_to == "Sales Agent 1"


    # =====================================
    # 3. QUALIFY LEAD
    # =====================================

    qualification = manager.qualify_lead(
        lead
    )

    print("\n3. Lead Qualification")
    print(qualification)

    assert qualification.qualified
    assert lead.status == LeadStatus.QUALIFIED


    # =====================================
    # 4. SCORE LEAD
    # =====================================

    score = manager.score_lead(
        lead
    )

    print("\n4. Lead Score")
    print(score)

    assert lead.score > 0


    # =====================================
    # 5. UPDATE STATUS
    # =====================================

    status = manager.update_status(
        lead,
        LeadStatus.CONVERTED,
    )

    print("\n5. Status Update")
    print(status)

    assert lead.status == LeadStatus.CONVERTED


    # =====================================
    # 6. SEARCH
    # =====================================

    leads = [
        lead
    ]

    results = manager.search_leads(
        leads,
        query="Mary",
    )

    print("\n6. Search Results")
    print(results)

    assert len(results) == 1


    print(
        "\n================================="
    )

    print(
        "✅ Lead Management Functional Test Passed"
    )

    print(
        "================================="
    )


if __name__ == "__main__":
    run()