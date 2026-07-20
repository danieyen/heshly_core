from heshly_core.models.crm import Lead
from heshly_core.services.crm.lead_validator import LeadValidator


def run():

    validator = LeadValidator()

    lead = Lead(
        lead_id="LEAD-001",
        business_id="BIZ-001",
        full_name="John Doe",
        phone="+254700123456",
        email="john@example.com",
    )

    result = validator.validate(lead)

    print(result)

    assert result.valid

    bad_lead = Lead(
        lead_id="",
        business_id="",
        full_name="",
        phone="123",
        email="bad-email",
        score=120,
    )

    result = validator.validate(bad_lead)

    print(result)

    assert not result.valid

    print()

    print("Errors")

    for error in result.errors:
        print("-", error)

    print()

    print("✅ Lead Validator Functional Test Passed")


if __name__ == "__main__":
    run()