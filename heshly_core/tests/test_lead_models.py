from heshly_core.models.lead import (
    LeadProfile,
    LeadAssignment,
    LeadQualification,
    LeadScore,
)


def run():

    lead = LeadProfile(
        lead_id="LEAD-001",
        full_name="John Doe",
        phone="+254700123456",
    )

    print(lead)

    assignment = LeadAssignment(
        lead_id=lead.lead_id,
        assigned_to="Sales Team",
    )

    print(assignment)

    qualification = LeadQualification(
        lead_id=lead.lead_id,
        qualified=True,
        confidence=0.94,
        reason="Customer requested quotation",
    )

    print(qualification)

    score = LeadScore(
        lead_id=lead.lead_id,
        score=92,
        reason="AI qualification",
    )

    print(score)

    print("\n✅ Lead Models Functional Test Passed")


if __name__ == "__main__":
    run()