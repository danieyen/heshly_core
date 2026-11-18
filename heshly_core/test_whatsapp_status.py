import frappe

from heshly_core.models.whatsapp import WhatsAppConfiguration

from heshly_core.services.whatsapp.webhook.webhook_event_parser import (
    WhatsAppWebhookEventParser,
)

from heshly_core.services.whatsapp.webhook.webhook_router import (
    WhatsAppWebhookRouter,
)

from heshly_core.repositories.whatsapp_activity_repository import (
    WhatsAppActivityRepository,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppActivityLogger,
)


MESSAGE_ID = "wamid.WEBHOOK-INTEGRATION-005"
PHONE = "254700000001"
TENANT_ID = "heshly"
BUSINESS_ID = "HESHLY"


def make_payload(status):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "TEST-WABA-ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "254700000000",
                                "phone_number_id": "TEST-PHONE-ID",
                            },
                            "statuses": [
                                {
                                    "id": MESSAGE_ID,
                                    "status": status,
                                    "timestamp": "1786620000",
                                    "recipient_id": PHONE,
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def main():

    print("=" * 80)
    print("WHATSAPP STATUS WEBHOOK INTEGRATION TEST")
    print("=" * 80)

    # --------------------------------------------------------
    # REAL RUNTIME CONFIGURATION CONTRACT
    # --------------------------------------------------------

    configuration = WhatsAppConfiguration(
        configuration_id="TEST-CONFIG-005",
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

    assert configuration.tenant_id == TENANT_ID
    assert configuration.business_id == BUSINESS_ID
    assert configuration.phone_number_id == "TEST-PHONE-ID"

    print()
    print("CONFIGURATION")
    print(" tenant_id      =", configuration.tenant_id)
    print(" business_id    =", configuration.business_id)
    print(" phone_number_id=", configuration.phone_number_id)

    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CREATE OUTBOUND ACTIVITY
    # --------------------------------------------------------

    logger = WhatsAppActivityLogger(
        tenant_id=TENANT_ID,
    )

    created = logger.log_message(
        business_id=BUSINESS_ID,
        related_type="WhatsApp Conversation",
        related_id=f"{TENANT_ID}:{PHONE}",
        direction="outbound",
        phone_number=PHONE,
        message="Webhook status integration test",
        status="sent",
        message_id=MESSAGE_ID,
    )

    print()
    print("CREATED OUTBOUND")
    print(" activity_id =", created.activity_id)
    print(" status      =", created.status)

    assert created.status == "sent"

    # --------------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------------

    parser = WhatsAppWebhookEventParser()
    router = WhatsAppWebhookRouter()

    repo = WhatsAppActivityRepository(
        tenant_id=TENANT_ID,
    )

    # --------------------------------------------------------
    # SENT
    # --------------------------------------------------------

    print()
    print("1. SENT")

    event = parser.parse(
        make_payload("sent")
    )

    print(" event_type =", event.event_type)
    print(" event      =", event)

    result = router.route(
        event,
        configuration,
    )

    print(" result     =", result)

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print(" db status  =", activity.status)

    assert activity is not None
    assert activity.status == "sent"

    # --------------------------------------------------------
    # DELIVERED
    # --------------------------------------------------------

    print()
    print("2. DELIVERED")

    event = parser.parse(
        make_payload("delivered")
    )

    result = router.route(
        event,
        configuration,
    )

    print(" result     =", result)

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print(" db status  =", activity.status)

    assert activity is not None
    assert activity.status == "delivered"

    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    print()
    print("3. READ")

    event = parser.parse(
        make_payload("read")
    )

    result = router.route(
        event,
        configuration,
    )

    print(" result     =", result)

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print(" db status  =", activity.status)

    assert activity is not None
    assert activity.status == "read"

    # --------------------------------------------------------
    # DUPLICATE READ
    # --------------------------------------------------------

    print()
    print("4. DUPLICATE READ")

    event = parser.parse(
        make_payload("read")
    )

    result = router.route(
        event,
        configuration,
    )

    print(" result     =", result)

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print(" db status  =", activity.status)

    assert activity is not None
    assert activity.status == "read"

    # --------------------------------------------------------
    # OUT-OF-ORDER SENT
    # --------------------------------------------------------

    print()
    print("5. OUT-OF-ORDER SENT")

    event = parser.parse(
        make_payload("sent")
    )

    result = router.route(
        event,
        configuration,
    )

    print(" result     =", result)

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print(" db status  =", activity.status)

    assert activity is not None
    assert activity.status == "read"

    # --------------------------------------------------------
    # OUT-OF-ORDER DELIVERED
    # --------------------------------------------------------

    print()
    print("6. OUT-OF-ORDER DELIVERED")

    event = parser.parse(
        make_payload("delivered")
    )

    result = router.route(
        event,
        configuration,
    )

    print(" result     =", result)

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print(" db status  =", activity.status)

    assert activity is not None
    assert activity.status == "read"

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    activity = repo.find_by_message_id(
        MESSAGE_ID
    )

    print()
    print("=" * 80)
    print("FINAL DATABASE STATE")
    print("=" * 80)

    print(" activity_id =", activity.activity_id)
    print(" business_id =", activity.business_id)
    print(" direction   =", activity.direction)
    print(" message_id  =", activity.message_id)
    print(" status      =", activity.status)

    assert activity.business_id == BUSINESS_ID
    assert activity.direction == "outbound"
    assert activity.message_id == MESSAGE_ID
    assert activity.status == "read"

    print()
    print("=" * 80)
    print("WEBHOOK STATUS INTEGRATION PASSED")
    print("=" * 80)
    print("Meta payload")
    print("    -> parser")
    print("    -> MessageStatusEvent")
    print("    -> webhook router")
    print("    -> status processor")
    print("    -> tenant-scoped repository")
    print("    -> database")
    print()
    print("sent -> delivered -> read")
    print("duplicate read preserved")
    print("out-of-order sent preserved")
    print("out-of-order delivered preserved")
    print("=" * 80)


if __name__ == "__main__":
    main()
