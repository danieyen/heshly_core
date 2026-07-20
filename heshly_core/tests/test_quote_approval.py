from heshly_core.models.quote import (
    Quote,
    QuoteItem,
    QuoteItemType,
    QuoteStatus,
)

from heshly_core.services.crm.quote_approval import (
    QuoteApproval,
)


def run():

    approval = QuoteApproval(
        auto_approve_limit=10000
    )

    quote = Quote(

        quote_id="QUOTE-001",

        business_id="BIZ-001",

        customer_id="CUS-001",

        title="Dental Quote",

    )

    quote.add_item(

        QuoteItem(

            item_id="ITEM-001",

            item_type=QuoteItemType.SERVICE,

            name="Dental Implant",

            quantity=1,

            unit_price=15000,

            tax_rate=16,

        )

    )

    assert approval.requires_approval(
        quote
    )

    approval.submit(
        quote
    )

    approval.approve(

        quote,

        "Manager",

    )

    assert (
        quote.status
        == QuoteStatus.SENT
    )

    approval.accept(
        quote
    )

    assert (
        quote.status
        == QuoteStatus.ACCEPTED
    )

    history = approval.history(
        quote
    )

    print(history)

    assert len(history) == 3

    print(
        "\n✅ Quote Approval Functional Test Passed"
    )


if __name__ == "__main__":

    run()