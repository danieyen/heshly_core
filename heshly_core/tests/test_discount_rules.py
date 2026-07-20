from heshly_core.models.quote import (
    Quote,
    QuoteItem,
    QuoteItemType,
)

from heshly_core.services.crm.discount_rules import (
    DiscountRules,
)


def run():

    rules = DiscountRules()

    quote = Quote(

        quote_id="Q-001",

        business_id="BIZ-001",

        customer_id="CUS-001",

        title="Dental Quote",

    )

    item = QuoteItem(

        item_id="ITEM-001",

        item_type=QuoteItemType.SERVICE,

        name="Dental Cleaning",

        quantity=20,

        unit_price=2500,

        tax_rate=16,

    )

    quote.add_item(item)

    rules.apply_volume_discount(item)

    rules.apply_coupon(

        quote,

        "WELCOME10",

    )

    print(rules.summary(quote))

    assert quote.discount_total > 0

    assert quote.grand_total > 0

    print("\n✅ Discount Rules Functional Test Passed")


if __name__ == "__main__":
    run()