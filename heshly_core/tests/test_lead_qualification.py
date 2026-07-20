from heshly_core.models.crm import Lead, LeadStatus

from heshly_core.services.crm.lead_qualification_manager import (
    LeadQualificationManager,
)


def run():

    manager = LeadQualificationManager()


    # Qualified Lead

    lead = Lead(
        lead_id="LEAD-001",
        business_id="BIZ-001",
        full_name="John Doe",
        phone="+254700123456",
    )


    result = manager.qualify(lead)

    print(result)

    assert result.qualified
    assert lead.status == LeadStatus.QUALIFIED


    # Unqualified Lead

    bad_lead = Lead(
        lead_id="LEAD-002",
        business_id="BIZ-001",
        full_name="",
    )


    result = manager.qualify(bad_lead)

    print(result)

    assert not result.qualified
    assert bad_lead.status == LeadStatus.UNQUALIFIED


    print(
        "\n✅ Lead Qualification Functional Test Passed"
    )


if __name__ == "__main__":
    run()