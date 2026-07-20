from heshly_core.services.crm.opportunity_creator import (
    OpportunityCreator,
    OpportunityCreationError,
)


def run():

    creator = OpportunityCreator()


    # -----------------------------
    # Valid Opportunity
    # -----------------------------

    opportunity = creator.create(
        lead_id="LEAD-001",
        title="Dental Implant Package",
        expected_value=150000,
        pipeline_id="PIPE-001",
        stage_id="STAGE-001",
    )


    print("Created Opportunity:")
    print(opportunity)


    assert opportunity.opportunity_id.startswith(
        "OPP-"
    )

    assert opportunity.title == (
        "Dental Implant Package"
    )

    assert opportunity.expected_value == 150000


    # -----------------------------
    # Invalid Opportunity
    # -----------------------------

    try:

        creator.create(
            lead_id="",
            title="",
            expected_value=-100,
        )

    except OpportunityCreationError as error:

        print("\nExpected Error:")
        print(error)


    else:

        raise Exception(
            "Invalid opportunity should fail"
        )


    print(
        "\n✅ Opportunity Creation Functional Test Passed"
    )


if __name__ == "__main__":
    run()