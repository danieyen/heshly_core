from __future__ import annotations

from datetime import date, timedelta

from heshly_core.models.quote import (
    QuoteItem,
    QuoteItemType,
    QuoteStatus,
)

from heshly_core.services.crm.quote_generator import (
    QuoteGenerator,
)

from heshly_core.services.crm.quote_items import (
    QuoteItems,
)

from heshly_core.services.crm.pricing_rules import (
    PricingRules,
)

from heshly_core.services.crm.discount_rules import (
    DiscountRules,
)

from heshly_core.services.crm.quote_approval import (
    QuoteApproval,
)

from heshly_core.services.crm.quote_status_tracker import (
    QuoteStatusTracker,
)


def run():

    print("=" * 60)
    print(" HESHLY QUOTE MANAGER FUNCTIONAL TEST")
    print("=" * 60)

    generator = QuoteGenerator()

    item_manager = QuoteItems()

    pricing = PricingRules()

    discounts = DiscountRules()

    approval = QuoteApproval(
        auto_approve_limit=50000
    )

    tracker = QuoteStatusTracker()

    # =====================================================
    # Create Quote
    # =====================================================

    quote = generator.create(

        business_id="BIZ-001",

        customer_id="CUS-001",

        opportunity_id="OPP-001",

        title="Complete Dental Treatment",

        expiry_date=date.today() + timedelta(days=14),

        created_by="Sales Agent",

    )

    print("✓ Quote Created")

    # =====================================================
    # Add Items
    # =====================================================

    item_manager.add_item(

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

    item_manager.add_item(

        quote,

        QuoteItem(

            item_id="ITEM-002",

            item_type=QuoteItemType.SERVICE,

            name="Tooth Extraction",

            quantity=2,

            unit_price=5000,

            tax_rate=16,

        ),

    )

    item_manager.add_item(

        quote,

        QuoteItem(

            item_id="ITEM-003",

            item_type=QuoteItemType.PRODUCT,

            name="Dental Kit",

            quantity=3,

            unit_price=800,

            tax_rate=16,

        ),

    )

    print("✓ Quote Items Added")

    # =====================================================
    # Pricing
    # =====================================================

    pricing.apply_quote_tax(

        quote,

        16,

    )

    print("✓ Tax Applied")

    # =====================================================
    # Discounts
    # =====================================================

    discounts.apply_customer_discount(

        quote,

        "gold",

    )

    print("✓ Customer Discount Applied")

    # =====================================================
    # Totals
    # =====================================================

    print("\nFinancial Summary")

    print("----------------------------")

    print(f"Items       : {quote.total_items}")

    print(f"Subtotal    : {quote.subtotal}")

    print(f"Discount    : {quote.discount_total}")

    print(f"Tax         : {quote.tax_total}")

    print(f"Grand Total : {quote.grand_total}")

    # =====================================================
    # Approval
    # =====================================================

    approval.submit(
        quote
    )

    if approval.requires_approval(
        quote
    ):

        approval.approve(

            quote,

            "Sales Manager",

        )

    print("✓ Quote Approved")

    # =====================================================
    # Status Tracking
    # =====================================================

    tracker.mark_sent(

        quote,

        "Sales Agent",

    )

    tracker.mark_accepted(

        quote,

        "Customer",

    )

    print("✓ Status Updated")

    # =====================================================
    # Validation
    # =====================================================

    assert quote.total_items == 3

    assert quote.subtotal > 0

    assert quote.tax_total > 0

    assert quote.discount_total > 0

    assert quote.grand_total > 0

    assert quote.status == QuoteStatus.ACCEPTED

    history = tracker.history(
        quote.quote_id
    )

    assert len(history) == 2

    print("\nStatus History")

    print("----------------------------")

    for event in history:

        print(

            f"{event['previous_status'].value}"

            f" -> "

            f"{event['new_status'].value}"

            f" ({event['changed_by']})"

        )

    print("\nApproval History")

    print("----------------------------")

    for record in approval.history(
        quote
    ):

        print(record)

    print("\n" + "=" * 60)

    print("✅ QUOTE MANAGER FUNCTIONAL TEST PASSED")

    print("=" * 60)


if __name__ == "__main__":

    run()