from heshly_core.models.quote import (
    Quote,
    QuoteItem,
    QuoteItemType,
)

from heshly_core.services.crm.quote_items import (
    QuoteItems,
)


def run():

    manager = QuoteItems()

    quote = Quote(

        quote_id="Q-001",

        business_id="BIZ-001",

        customer_id="CUS-001",

        title="Dental Services",

    )

    item = QuoteItem(

        item_id="ITEM-001",

        item_type=QuoteItemType.SERVICE,

        name="Dental Cleaning",

        quantity=1,

        unit_price=5000,

        discount=10,

        tax_rate=16,

    )

    manager.add_item(
        quote,
        item,
    )

    assert manager.item_count(quote) == 1

    manager.set_quantity(
        quote,
        "ITEM-001",
        2,
    )

    manager.set_unit_price(
        quote,
        "ITEM-001",
        6000,
    )

    manager.set_discount(
        quote,
        "ITEM-001",
        5,
    )

    manager.set_tax_rate(
        quote,
        "ITEM-001",
        16,
    )

    print("Items:", manager.item_count(quote))
    print("Subtotal:", manager.subtotal(quote))
    print("Discount:", manager.discount_total(quote))
    print("Tax:", manager.tax_total(quote))
    print("Grand Total:", manager.grand_total(quote))

    assert manager.grand_total(quote) > 0

    manager.remove_item(
        quote,
        "ITEM-001",
    )

    assert manager.item_count(quote) == 0

    print("\n✅ Quote Items Functional Test Passed")


if __name__ == "__main__":
    run()