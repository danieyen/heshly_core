from heshly_core.models.crm import Lead, LeadStatus

from heshly_core.services.crm.lead_status_manager import (
    LeadStatusManager,
    LeadStatusError,
)


def run():

    manager = LeadStatusManager()


    lead = Lead(
        lead_id="LEAD-001",
        business_id="BIZ-001",
        full_name="John Doe",
    )


    # NEW -> CONTACTED

    result = manager.change_status(
        lead,
        LeadStatus.CONTACTED,
    )

    print(result)

    assert lead.status == LeadStatus.CONTACTED


    # CONTACTED -> QUALIFIED

    result = manager.change_status(
        lead,
        LeadStatus.QUALIFIED,
    )

    print(result)

    assert lead.status == LeadStatus.QUALIFIED


    # QUALIFIED -> CONVERTED

    result = manager.convert(lead)

    print(result)

    assert lead.status == LeadStatus.CONVERTED


    # Invalid transition

    try:

        manager.change_status(
            lead,
            LeadStatus.NEW,
        )

    except LeadStatusError as error:

        print("\nExpected Error:")
        print(error)


    else:
        raise Exception(
            "Invalid transition should fail"
        )


    print(
        "\n✅ Lead Status Management Functional Test Passed"
    )


if __name__ == "__main__":
    run()