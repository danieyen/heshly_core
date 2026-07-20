from heshly_core.models.quote import (
    Quote,
    QuoteStatus,
)

from heshly_core.services.crm.quote_status_tracker import (
    QuoteStatusTracker,
)


def run():

    print("=" * 60)
    print("QUOTE STATUS TRACKER TEST")
    print("=" * 60)

    tracker = QuoteStatusTracker()

    quote = Quote(

        quote_id="QUOTE-001",

        business_id="BIZ-001",

        customer_id="CUS-001",

        title="Dental Quote",

    )

    tracker.mark_sent(
        quote,
        "Receptionist",
    )

    tracker.mark_accepted(
        quote,
        "Customer",
    )

    history = tracker.history(
        quote.quote_id
    )

    assert (
        quote.status
        == QuoteStatus.ACCEPTED
    )

    assert len(history) == 2

    assert tracker.is_final(
        quote
    )

    print("Current Status:", quote.status.value)
    print("Transitions:", len(history))

    for event in history:

        print(event)

    print("\n✅ Quote Status Tracker Test Passed")


if __name__ == "__main__":
    run()