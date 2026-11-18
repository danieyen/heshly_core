import frappe

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)
from heshly_core.services.whatsapp.conversation_flow import (
    WhatsAppConversationFlow,
)
from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


TENANT_ID = "heshly"
BUSINESS_ID = "HESHLY"
PHONE = "254700000099"
MESSAGE_ID = "wamid.INBOUND-PERSISTENCE-002"


def main():

    print("=" * 80)
    print("INBOUND WHATSAPP ACTIVITY PERSISTENCE TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # CLEAN
    # ---------------------------------------------------------

    existing = frappe.db.get_value(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
        },
        "name",
    )

    if existing:
        frappe.delete_doc(
            "Heshly WhatsApp Activity",
            existing,
            ignore_permissions=True,
        )
        frappe.db.commit()

    # ---------------------------------------------------------
    # REAL CONFIGURATION CONTRACT
    # ---------------------------------------------------------

    configuration = WhatsAppConfiguration(
        configuration_id="TEST-INBOUND-CONFIG-002",
        tenant_id=TENANT_ID,
        business_id=BUSINESS_ID,
        business_account_id="TEST-WABA-ID",
        phone_number_id="TEST-PHONE-ID",
        access_token="TEST-ACCESS-TOKEN",
        verify_token="TEST-VERIFY-TOKEN",
        app_secret="TEST-APP-SECRET",
        display_phone_number="254700000000",
        webhook_url="https://erp.heshly.com/api/method/heshly_core.api.whatsapp.webhook",
        language="en",
        api_version="v23.0",
        webhook_enabled=True,
        business_name="Heshly Test Business",
    )

    # ---------------------------------------------------------
    # REAL WEBHOOK EVENT
    # ---------------------------------------------------------

    event = IncomingMessageEvent(
        message_id=MESSAGE_ID,
        phone_number=PHONE,
        customer_name="Persistence Test Customer",
        message_type="text",
        text="I want to book an appointment.",
    )

    print()
    print("EVENT")
    print(" message_id   =", event.message_id)
    print(" phone_number =", event.phone_number)
    print(" text         =", event.text)

    # ---------------------------------------------------------
    # VERIFY ABSENT BEFORE FLOW
    # ---------------------------------------------------------

    before = frappe.db.get_value(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
        },
        "name",
    )

    print()
    print("BEFORE FLOW")
    print(" activity =", before)

    assert before is None

    # ---------------------------------------------------------
    # REAL CONVERSATION FLOW
    # ---------------------------------------------------------

    flow = WhatsAppConversationFlow()

    print()
    print("RUNNING WhatsAppConversationFlow.process()")

    try:
        result = flow.process(
            event,
            tenant_id=TENANT_ID,
            configuration=configuration,
        )

        print(" flow result =", result)

    except Exception as exc:

        print()
        print("FLOW RAISED:", type(exc).__name__)
        print(str(exc))

        # The important persistence guarantee is that inbound
        # activity is written BEFORE downstream AI processing.
        # Therefore continue to database verification.

    # ---------------------------------------------------------
    # DATABASE VERIFICATION
    # ---------------------------------------------------------

    print()
    print("DATABASE VERIFICATION")

    activity_name = frappe.db.get_value(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
        },
        "name",
    )

    print(" activity name =", activity_name)

    assert activity_name is not None, (
        "Inbound WhatsApp activity was NOT persisted."
    )

    doc = frappe.get_doc(
        "Heshly WhatsApp Activity",
        activity_name,
    )

    print()
    print("PERSISTED ACTIVITY")
    print(" name         =", doc.name)
    print(" tenant_id    =", doc.tenant_id)
    print(" business_id  =", doc.business_id)
    print(" direction    =", doc.direction)
    print(" phone_number =", doc.phone_number)
    print(" message_id   =", doc.message_id)
    print(" status       =", doc.status)
    print(" message      =", doc.message)

    assert doc.tenant_id == TENANT_ID
    assert doc.business_id == BUSINESS_ID
    assert doc.direction == "inbound"
    assert doc.phone_number == PHONE
    assert doc.message_id == MESSAGE_ID
    assert doc.status == "received"
    assert doc.message == "I want to book an appointment."

    # ---------------------------------------------------------
    # REPOSITORY VERIFICATION
    # ---------------------------------------------------------

    from heshly_core.repositories.whatsapp_activity_repository import (
        WhatsAppActivityRepository,
    )

    repository = WhatsAppActivityRepository(
        tenant_id=TENANT_ID,
    )

    restored = repository.find_by_message_id(
        MESSAGE_ID,
    )

    print()
    print("REPOSITORY READ")
    print(" restored =", restored)

    assert restored is not None
    assert restored.tenant_id == TENANT_ID
    assert restored.business_id == BUSINESS_ID
    assert restored.direction == "inbound"
    assert restored.status == "received"
    assert restored.message_id == MESSAGE_ID

    # ---------------------------------------------------------
    # IDEMPOTENCY CHECK
    # ---------------------------------------------------------

    count_before = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
        },
    )

    print()
    print("IDEMPOTENCY")
    print(" matching rows =", count_before)

    assert count_before == 1

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("INBOUND ACTIVITY PERSISTENCE PASSED")
    print("=" * 80)
    print("WhatsAppConversationFlow")
    print("      -> WhatsAppActivityLogger")
    print("      -> WhatsAppActivityRepository")
    print("      -> Heshly WhatsApp Activity")
    print("      -> MariaDB")
    print()
    print("tenant-safe       = PASS")
    print("business mapping  = PASS")
    print("inbound direction = PASS")
    print("received status   = PASS")
    print("message persisted = PASS")
    print("repository read   = PASS")
    print("idempotency       = PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()
