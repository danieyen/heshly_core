from heshly_core.models.crm import Opportunity

from heshly_core.services.crm.opportunity_probability_manager import (
    OpportunityProbabilityManager,
    OpportunityProbabilityError,
)


def run():

    manager = OpportunityProbabilityManager()


    opportunity = Opportunity(
        opportunity_id="OPP-001",
        lead_id="LEAD-001",
        title="Dental Implant Package",
        probability=0.10,
    )


    # Update probability

    result = manager.update_probability(
        opportunity,
        0.75,
        "Customer requested quotation",
    )


    print(result)


    assert opportunity.probability == 0.75

    assert result.new_probability == 0.75


    # Invalid probability

    try:

        manager.update_probability(
            opportunity,
            1.5,
            "Invalid test",
        )


    except OpportunityProbabilityError as error:

        print("\nExpected Error:")
        print(error)


    else:

        raise Exception(
            "Invalid probability should fail"
        )


    print(
        "\n✅ Opportunity Probability Functional Test Passed"
    )


if __name__ == "__main__":
    run()