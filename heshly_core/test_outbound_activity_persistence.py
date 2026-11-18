import frappe

from heshly_core.models.whatsapp import WhatsAppConfiguration
from heshly_core.services.whatsapp.conversation_flow import (
    WhatsAppConversationFlow,
)
from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


TENANT_ID = "heshly"
BUSINESS_ID = "HESHLY"

# UNIQUE conversation for this test
PHONE = "254700000098"
MESSAGE_ID = "wamid.OUTBOUND-PERSISTENCE-003"

RELATED_ID = f"{TENANT_ID}:{PHONE}"

EXPECTED_INBOUND = "I want to book an appointment."
EXPECTED_REPLY = "Sure. What service would you like to book?"


def main():

    print("=" * 80)
    print("OUTBOUND WHATSAPP ACTIVITY PERSISTENCE TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # CLEAN ONLY THIS TEST CONVERSATION
    # ---------------------------------------------------------

    names = frappe.db.get_all(
        "Heshly WhatsApp Activity",
        filters={
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
        },
        pluck="name",
    )

    for name in names:
        frappe.delete_doc(
            "Heshly WhatsApp Activity",
            name,
            ignore_permissions=True,
        )

    frappe.db.commit()

    # ---------------------------------------------------------
    # CONFIGURATION
    # ---------------------------------------------------------

    configuration = WhatsAppConfiguration(
        configuration_id="TEST-OUTBOUND-CONFIG-003",
        tenant_id=TENANT_ID,
        business_id=BUSINESS_ID,
        business_account_id="TEST-WABA-ID",
        phone_number_id="TEST-PHONE-ID",
        access_token="TEST-ACCESS-TOKEN",
        verify_token="TEST-VERIFY-TOKEN",
        app_secret="TEST-APP-SECRET",
        display_phone_number="254700000000",
        webhook_url=(
            "https://erp.heshly.com/"
            "api/method/heshly_core.api.whatsapp.webhook"
        ),
        language="en",
        api_version="v23.0",
        webhook_enabled=True,
        business_name="Heshly Test Business",
    )

    # ---------------------------------------------------------
    # INBOUND EVENT
    # ---------------------------------------------------------

    event = IncomingMessageEvent(
        message_id=MESSAGE_ID,
        phone_number=PHONE,
        customer_name="Outbound Persistence Test",
        message_type="text",
        text=EXPECTED_INBOUND,
    )

    print()
    print("EVENT")
    print(" message_id   =", event.message_id)
    print(" phone_number =", event.phone_number)
    print(" text         =", event.text)

    # ---------------------------------------------------------
    # VERIFY CLEAN
    # ---------------------------------------------------------

    before = frappe.db.get_all(
        "Heshly WhatsApp Activity",
        filters={
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
        },
        fields=[
            "name",
            "direction",
            "status",
            "message",
        ],
    )

    print()
    print("BEFORE FLOW")
    print(" activities =", before)

    assert before == []

    # ---------------------------------------------------------
    # RUN REAL FLOW
    # ---------------------------------------------------------

    flow = WhatsAppConversationFlow()

    print()
    print("RUNNING WhatsAppConversationFlow.process()")

    result = flow.process(
        event,
        tenant_id=TENANT_ID,
        configuration=configuration,
    )

    orchestration = result["orchestration"]
    send_result = result["send_result"]

    print()
    print("FLOW RESULT")
    print(" orchestration =", orchestration)
    print(" send_result   =", send_result)

    # ---------------------------------------------------------
    # VERIFY AI RESPONSE
    # ---------------------------------------------------------

    reply = (
        orchestration
        .get("response", {})
        .get("reply")
    )

    print()
    print("AI RESPONSE")
    print(" reply =", reply)

    assert reply == EXPECTED_REPLY

    # ---------------------------------------------------------
    # READ ONLY THIS CONVERSATION
    # ---------------------------------------------------------

    rows = frappe.db.get_all(
        "Heshly WhatsApp Activity",
        filters={
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
        },
        fields=[
            "name",
            "tenant_id",
            "business_id",
            "related_type",
            "related_id",
            "message_id",
            "direction",
            "phone_number",
            "message",
            "status",
        ],
        order_by="creation asc",
    )

    print()
    print("CONVERSATION ACTIVITIES")

    for index, row in enumerate(rows, start=1):
        print(
            f" {index}: "
            f"direction={row.direction!r}, "
            f"status={row.status!r}, "
            f"message_id={row.message_id!r}, "
            f"message={row.message!r}"
        )

    # ---------------------------------------------------------
    # EXPECT EXACTLY TWO ACTIVITIES
    # ---------------------------------------------------------

    assert len(rows) == 2, (
        f"Expected exactly 2 activities "
        f"(1 inbound + 1 outbound), got {len(rows)}."
    )

    inbound = [
        row
        for row in rows
        if row.direction == "inbound"
    ]

    outbound = [
        row
        for row in rows
        if row.direction == "outbound"
        and row.message == EXPECTED_REPLY
    ]

    print()
    print("INBOUND COUNT")
    print(" count =", len(inbound))

    print()
    print("OUTBOUND AI COUNT")
    print(" count =", len(outbound))

    assert len(inbound) == 1
    assert len(outbound) == 1

    # ---------------------------------------------------------
    # VERIFY INBOUND
    # ---------------------------------------------------------

    inbound_activity = inbound[0]

    assert inbound_activity.tenant_id == TENANT_ID
    assert inbound_activity.business_id == BUSINESS_ID
    assert inbound_activity.related_type == "WhatsApp Conversation"
    assert inbound_activity.related_id == RELATED_ID
    assert inbound_activity.direction == "inbound"
    assert inbound_activity.phone_number == PHONE
    assert inbound_activity.message_id == MESSAGE_ID
    assert inbound_activity.message == EXPECTED_INBOUND
    assert inbound_activity.status == "received"

    # ---------------------------------------------------------
    # VERIFY OUTBOUND
    # ---------------------------------------------------------

    outbound_activity = outbound[0]

    print()
    print("OUTBOUND PERSISTED ACTIVITY")
    print(" name         =", outbound_activity.name)
    print(" tenant_id    =", outbound_activity.tenant_id)
    print(" business_id  =", outbound_activity.business_id)
    print(" related_type =", outbound_activity.related_type)
    print(" related_id   =", outbound_activity.related_id)
    print(" message_id   =", outbound_activity.message_id)
    print(" direction    =", outbound_activity.direction)
    print(" phone_number =", outbound_activity.phone_number)
    print(" status       =", outbound_activity.status)
    print(" message      =", outbound_activity.message)

    assert outbound_activity.tenant_id == TENANT_ID
    assert outbound_activity.business_id == BUSINESS_ID
    assert outbound_activity.related_type == "WhatsApp Conversation"
    assert outbound_activity.related_id == RELATED_ID
    assert outbound_activity.direction == "outbound"
    assert outbound_activity.phone_number == PHONE
    assert outbound_activity.message == EXPECTED_REPLY

    # Fake token means Meta send fails, but the attempt MUST persist.
    assert outbound_activity.status == "failed"

    # Outbound activity must have its own activity/message identifier.
    assert outbound_activity.message_id
    assert outbound_activity.message_id != MESSAGE_ID

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
        outbound_activity.message_id,
    )

    print()
    print("REPOSITORY READ")
    print(" restored =", restored)

    assert restored is not None
    assert restored.business_id == BUSINESS_ID
    assert restored.related_id == RELATED_ID
    assert restored.direction == "outbound"
    assert restored.status == "failed"
    assert restored.message == EXPECTED_REPLY

    # ---------------------------------------------------------
    # OUTBOUND MESSAGE ID UNIQUENESS
    # ---------------------------------------------------------

    count = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": outbound_activity.message_id,
        },
    )

    print()
    print("OUTBOUND MESSAGE-ID ROW COUNT")
    print(" matching rows =", count)

    assert count == 1

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("OUTBOUND ACTIVITY PERSISTENCE PASSED")
    print("=" * 80)
    print("ConversationFlow")
    print("      -> AI orchestration")
    print("      -> WhatsAppOutgoingMessageSender")
    print("      -> WhatsAppActivityLogger")
    print("      -> WhatsAppActivityRepository")
    print("      -> Heshly WhatsApp Activity")
    print("      -> MariaDB")
    print()
    print("AI response generated = PASS")
    print("inbound persisted     = PASS")
    print("outbound persisted    = PASS")
    print("outbound direction    = PASS")
    print("tenant mapping        = PASS")
    print("business mapping      = PASS")
    print("response persisted    = PASS")
    print("failed-send persisted = PASS")
    print("repository read       = PASS")
    print("message ID unique     = PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()
