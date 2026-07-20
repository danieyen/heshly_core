from heshly_core.models.crm import Lead, LeadStatus

from heshly_core.services.crm.lead_scoring_engine import (
    LeadScoringEngine,
)


def run():

    engine = LeadScoringEngine()


    # High quality lead

    lead = Lead(
        lead_id="LEAD-001",
        business_id="BIZ-001",
        full_name="John Doe",
        phone="+254700123456",
        email="john@example.com",
        company="ABC Ltd",
        status=LeadStatus.QUALIFIED,
    )


    result = engine.calculate(lead)

    print(result)

    assert result.new_score == 80
    assert lead.score == 80


    # Basic lead

    basic_lead = Lead(
        lead_id="LEAD-002",
        business_id="BIZ-001",
        full_name="Jane Doe",
        phone="+254700999999",
    )


    result = engine.calculate(basic_lead)

    print(result)

    assert result.new_score == 20


    print(
        "\n✅ Lead Scoring Functional Test Passed"
    )


if __name__ == "__main__":
    run()