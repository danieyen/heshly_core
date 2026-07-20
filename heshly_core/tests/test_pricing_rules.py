from heshly_core.models.quote import (
    Quote,
    QuoteItem,
    QuoteItemType,
)

from heshly_core.services.crm.pricing_rules import (
    PricingRules,
)


def run():

    rules = PricingRules()

    quote = Quote(

        quote_id="QUOTE-001",

        business_id="BIZ-001",

        customer_id="CUS-001",

        title="Dental Services",

    )

    item = QuoteItem(

        item_id="ITEM-001",

        item_type=QuoteItemType.SERVICE,

        name="Dental Cleaning",

        quantity=5,

        unit_price=3000,

    )

    quote.add_item(item)

    rules.apply_bulk_discount(

        item,

        minimum_quantity=5,

        discount=10,

    )

    rules.apply_tax(item)

    print(rules.summary(quote))

    assert quote.grand_total > 0

    print("\n✅ Pricing Rules Functional Test Passed")


if __name__ == "__main__":
    run()