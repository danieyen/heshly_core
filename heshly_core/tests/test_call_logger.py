from heshly_core.services.crm.call_logger import (
    CallLogger,
    CallDirection,
    CallOutcome,
)


def run():

    logger = CallLogger()


    call = logger.log_call(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        direction=CallDirection.OUTBOUND,

        phone_number="+254700123456",

        duration_seconds=420,

        outcome=CallOutcome.ANSWERED,

        notes="Customer requested a follow-up quotation.",

        logged_by="Sales Agent",

    )


    print("Created Call:")
    print(call)


    assert call.direction == CallDirection.OUTBOUND

    assert call.outcome == CallOutcome.ANSWERED

    assert call.duration_seconds == 420


    history = logger.get_calls(

        "opportunity",

        "OPP-001",

    )


    print("\nCall History:")
    print(history)


    assert len(history) == 1


    print(
        "\n✅ Call Logging Functional Test Passed"
    )


if __name__ == "__main__":

    run()