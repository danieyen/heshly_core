from heshly_core.services.crm.lead_creator import (
    LeadCreator,
    LeadCreationError,
)


def run():

    creator = LeadCreator()

    # -----------------------------
    # Valid Lead
    # -----------------------------

    lead = creator.create(
        business_id="BIZ-001",
        full_name="John Doe",
        phone="+254700123456",
        email="john@example.com",
        company="Example Ltd",
    )

    print("Created Lead")
    print(lead)

    assert lead.lead_id.startswith("LEAD-")
    assert lead.full_name == "John Doe"

    # -----------------------------
    # Invalid Lead
    # -----------------------------

    try:

        creator.create(
            business_id="",
            full_name="",
            phone="123",
            email="wrong-email",
        )

    except LeadCreationError as error:

        print("\nExpected Error")
        print(error)

    else:
        raise Exception(
            "Invalid lead should have failed"
        )

    print("\n✅ Lead Creation Functional Test Passed")


if __name__ == "__main__":
    run()