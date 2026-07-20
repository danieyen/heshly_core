from heshly_core.models.quote import (
    QuoteItem,
    QuoteItemType,
)

from heshly_core.services.crm.quote_generator import (
    QuoteGenerator,
)


def run():

    generator = QuoteGenerator()

    quote = generator.create(

        business_id="BIZ-001",

        customer_id="CUS-001",

        title="Dental Cleaning",

        created_by="Receptionist",

    )

    generator.add_item(

        quote,

        QuoteItem(

            item_id="ITEM-001",

            item_type=QuoteItemType.SERVICE,

            name="Dental Cleaning",

            quantity=1,

            unit_price=3500,

            tax_rate=16,

        ),

    )

    generator.add_item(

        quote,

        QuoteItem(

            item_id="ITEM-002",

            item_type=QuoteItemType.PRODUCT,

            name="Dental Kit",

            quantity=2,

            unit_price=500,

            discount=10,

            tax_rate=16,

        ),

    )

    print(quote)

    print("Subtotal:", quote.subtotal)

    print("Discount:", quote.discount_total)

    print("Tax:", quote.tax_total)

    print("Grand Total:", quote.grand_total)

    assert quote.total_items == 2

    assert quote.grand_total > 0

    print("\n✅ Quote Generator Functional Test Passed")


if __name__ == "__main__":

    run()