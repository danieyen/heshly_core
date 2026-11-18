import frappe
import json
import hmac
import hashlib

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


TENANT_ID = "heshly"
PHONE_NUMBER_ID = "1192499907286007"
PHONE_NUMBER_ID = "1192499907286007"
BUSINESS_ID = "HESHLY"
PHONE = "254700000097"
MESSAGE_ID = "wamid.E2E-INBOUND-001"

CONVERSATION_ID = f"{TENANT_ID}:{PHONE}"
RELATED_ID = CONVERSATION_ID

INBOUND_TEXT = "I want to book an appointment."
EXPECTED_REPLY = "Sure. What service would you like to book?"


def _clean():
    """Remove only this test's persisted data."""

    # ---------------------------------------------------------
    # WhatsApp activities
    # ---------------------------------------------------------

    activity_names = frappe.db.get_all(
        "Heshly WhatsApp Activity",
        filters={
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
        },
        pluck="name",
    )

    for name in activity_names:
        frappe.delete_doc(
            "Heshly WhatsApp Activity",
            name,
            ignore_permissions=True,
        )

    # ---------------------------------------------------------
    # AI Conversation
    # ---------------------------------------------------------

    conversation_name = frappe.db.get_value(
        "AI Conversation",
        {
            "tenant_id": TENANT_ID,
            "conversation_id": CONVERSATION_ID,
        },
        "name",
    )

    if conversation_name:
        frappe.delete_doc(
            "AI Conversation",
            conversation_name,
            ignore_permissions=True,
        )

    frappe.db.commit()


def _print_json(title, value):
    print()
    print(title)
    print(json.dumps(value, indent=2, default=str))


def main():

    print("=" * 80)
    print("REAL INBOUND WHATSAPP AI FLOW E2E TEST")
    print("=" * 80)

    # =========================================================
    # CLEAN
    # =========================================================

    print()
    print("CLEANING TEST DATA")

    _clean()

    # =========================================================
    # VERIFY TENANT
    # =========================================================

    business = frappe.db.get_value(
        "Business Account",
        {
            "tenant_id": TENANT_ID,
            "business_id": BUSINESS_ID,
        },
        [
            "name",
            "business_id",
            "tenant_id",
            "domain",
            "status",
        ],
        as_dict=True,
    )

    print()
    print("TENANT / BUSINESS")
    print(" business =", business)

    assert business is not None
    assert business.tenant_id == TENANT_ID
    assert business.business_id == BUSINESS_ID

    # =========================================================
    # BUILD REAL META WEBHOOK PAYLOAD
    # =========================================================

    payload = {
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
                                "phone_number_id": "1192499907286007",
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Real E2E Customer",
                                    },
                                    "wa_id": PHONE,
                                }
                            ],
                            "messages": [
                                {
                                    "from": PHONE,
                                    "id": MESSAGE_ID,
                                    "timestamp": "1755090000",
                                    "type": "text",
                                    "text": {
                                        "body": INBOUND_TEXT,
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    _print_json(
        "WEBHOOK PAYLOAD",
        payload,
    )

    # =========================================================
    # VERIFY ABSENT BEFORE WEBHOOK
    # =========================================================

    existing_activity = frappe.db.get_value(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
        },
        "name",
    )

    existing_conversation = frappe.db.get_value(
        "AI Conversation",
        {
            "tenant_id": TENANT_ID,
            "conversation_id": CONVERSATION_ID,
        },
        "name",
    )

    print()
    print("BEFORE WEBHOOK")
    print(" activity     =", existing_activity)
    print(" conversation =", existing_conversation)

    assert existing_activity is None
    assert existing_conversation is None

    # =========================================================
    # CALL REAL WEBHOOK ENTRYPOINT
    # =========================================================

    print()
    print("=" * 80)
    print("CALLING REAL WHATSAPP WEBHOOK ENTRYPOINT")
    print("=" * 80)

    import heshly_core.api.whatsapp as whatsapp_api

    print()
    print("WEBHOOK MODULE =", whatsapp_api.__file__)

    # ---------------------------------------------------------
    # Create real Werkzeug request
    # ---------------------------------------------------------

    from werkzeug.test import EnvironBuilder
    from werkzeug.wrappers import Request

    body = json.dumps(payload).encode()

    # ---------------------------------------------------------
    # Generate real Meta-style webhook signature
    # ---------------------------------------------------------

    # Resolve configuration through the same repository path
    # used by the real webhook.
    from heshly_core.repositories.whatsapp_configuration_repository import (
        WhatsAppConfigurationRepository,
    )

    configuration_repository = (
        WhatsAppConfigurationRepository()
    )

    configuration = (
        configuration_repository.get_by_phone_number_id(
            PHONE_NUMBER_ID
        )
    )

    if configuration is None:
        raise RuntimeError(
            f"No WhatsApp configuration found for "
            f"phone_number_id={PHONE_NUMBER_ID!r}"
        )

    if not configuration.app_secret:
        raise RuntimeError(
            "Resolved WhatsApp configuration has no app_secret"
        )

    signature = hmac.new(
        configuration.app_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    x_hub_signature = f"sha256={signature}"

    print()
    print("WEBHOOK SIGNATURE GENERATED")
    print(" algorithm = HMAC-SHA256")
    print(" signature  = sha256:<redacted>")

    builder = EnvironBuilder(
        method="POST",
        path="/api/method/heshly_core.api.whatsapp.webhook",
        base_url="https://erp.heshly.com",
        data=body,
        content_type="application/json",
        headers={
            "Host": "erp.heshly.com",
            "X-Hub-Signature-256": x_hub_signature,
        },
    )

    environ = builder.get_environ()
    request = Request(environ)

    old_request = getattr(
        frappe.local,
        "request",
        None,
    )

    frappe.local.request = request

    try:

        webhook = getattr(
            whatsapp_api,
            "webhook",
            None,
        )

        if webhook is None:
            raise RuntimeError(
                "heshly_core.api.whatsapp.webhook was not found."
            )

        print()
        print("WEBHOOK FUNCTION =", webhook)

        response = webhook()

        print()
        print("WEBHOOK RESPONSE")
        print(response)

    finally:

        if old_request is not None:
            frappe.local.request = old_request
        else:
            frappe.local.request = None

    # =========================================================
    # DUPLICATE WEBHOOK — SAME MESSAGE ID
    # =========================================================

    print()
    print("=" * 80)
    print("CALLING SAME WEBHOOK A SECOND TIME")
    print("=" * 80)

    # Count persisted records BEFORE duplicate.
    inbound_before = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
            "direction": "inbound",
        },
    )

    outbound_before = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "related_id": CONVERSATION_ID,
            "direction": "outbound",
        },
    )

    conversation_before = frappe.db.get_value(
        "AI Conversation",
        CONVERSATION_ID,
        "turn_count",
    )

    duplicate_builder = EnvironBuilder(
        method="POST",
        path="/api/method/heshly_core.api.whatsapp.webhook",
        base_url="https://erp.heshly.com",
        data=body,
        content_type="application/json",
        headers={
            "Host": "erp.heshly.com",
            "X-Hub-Signature-256": x_hub_signature,
        },
    )

    duplicate_environ = duplicate_builder.get_environ()
    duplicate_request = Request(duplicate_environ)

    old_request = getattr(
        frappe.local,
        "request",
        None,
    )

    frappe.local.request = duplicate_request

    try:
        duplicate_response = webhook()

        print()
        print("DUPLICATE WEBHOOK RESPONSE")
        print(duplicate_response)

    finally:
        if old_request is not None:
            frappe.local.request = old_request
        else:
            frappe.local.request = None

    # ---------------------------------------------------------
    # Verify duplicate response
    # ---------------------------------------------------------

    assert isinstance(
        duplicate_response,
        dict,
    ), (
        f"Expected dict duplicate response, "
        f"got {type(duplicate_response).__name__}"
    )

    assert duplicate_response["success"] is True

    assert (
        duplicate_response["message"]
        == "Duplicate webhook ignored."
    )

    assert (
        duplicate_response["metadata"]["duplicate"]
        is True
    )

    print()
    print("duplicate response = PASS")

    # ---------------------------------------------------------
    # Verify NO duplicate persistence
    # ---------------------------------------------------------

    inbound_after = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "message_id": MESSAGE_ID,
            "direction": "inbound",
        },
    )

    outbound_after = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "related_id": CONVERSATION_ID,
            "direction": "outbound",
        },
    )

    conversation_after = frappe.db.get_value(
        "AI Conversation",
        CONVERSATION_ID,
        "turn_count",
    )

    print()
    print("IDEMPOTENCY DATABASE CHECK")
    print(" inbound before =", inbound_before)
    print(" inbound after  =", inbound_after)
    print(" outbound before =", outbound_before)
    print(" outbound after  =", outbound_after)
    print(" turns before   =", conversation_before)
    print(" turns after    =", conversation_after)

    assert inbound_before == 1
    assert inbound_after == 1

    assert outbound_after == outbound_before

    assert conversation_after == conversation_before

    print()
    print("INBOUND ACTIVITY DUPLICATION = PASS")
    print("AI RESPONSE DUPLICATION       = PASS")
    print("CONVERSATION TURN DUPLICATION = PASS")

    # =========================================================
    # DATABASE VERIFICATION
    # =========================================================

    print()
    print("=" * 80)
    print("DATABASE VERIFICATION")
    print("=" * 80)

    # =========================================================
    # INBOUND ACTIVITY
    # =========================================================

    inbound = frappe.db.get_all(
        "Heshly WhatsApp Activity",
        filters={
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
            "direction": "inbound",
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
    )

    print()
    print("INBOUND ACTIVITIES")

    for row in inbound:
        print(row)

    assert len(inbound) == 1

    inbound_activity = inbound[0]

    assert inbound_activity.tenant_id == TENANT_ID
    assert inbound_activity.business_id == BUSINESS_ID
    assert inbound_activity.related_type == "WhatsApp Conversation"
    assert inbound_activity.related_id == RELATED_ID
    assert inbound_activity.message_id == MESSAGE_ID
    assert inbound_activity.direction == "inbound"
    assert inbound_activity.phone_number == PHONE
    assert inbound_activity.message == INBOUND_TEXT
    assert inbound_activity.status == "received"

    print(" inbound activity = PASS")

    # =========================================================
    # AI CONVERSATION
    # =========================================================

    print()
    print("AI CONVERSATION PERSISTENCE")

    conversation = frappe.get_doc(
        "AI Conversation",
        CONVERSATION_ID,
    )

    print()
    print("conversation.name =", conversation.name)
    print("conversation_id   =", conversation.conversation_id)
    print("tenant_id         =", conversation.tenant_id)
    print("customer_id       =", conversation.customer_id)
    print("channel           =", conversation.channel)
    print("status            =", conversation.status)
    print("turn_count        =", conversation.turn_count)
    print("started_at        =", conversation.started_at)
    print("last_message_at   =", conversation.last_message_at)

    assert conversation.name == CONVERSATION_ID
    assert conversation.conversation_id == CONVERSATION_ID
    assert conversation.tenant_id == TENANT_ID
    assert conversation.customer_id == PHONE
    assert conversation.channel == "whatsapp"

    # The inbound message and AI response should both be persisted.
    assert conversation.turn_count == 2
    assert len(conversation.turns) == 2

    print(" conversation persistence = PASS")

    # =========================================================
    # CONVERSATION TURNS
    # =========================================================

    print()
    print("AI CONVERSATION TURNS")

    turns = conversation.turns

    for index, turn in enumerate(turns, start=1):
        print(
            index,
            {
                "role": turn.role,
                "message": turn.message,
                "timestamp": turn.timestamp,
                "intent": turn.intent,
                "confidence": turn.confidence,
                "action": turn.action,
            },
        )

    # ---------------------------------------------------------
    # User turn
    # ---------------------------------------------------------

    user_turn = turns[0]

    assert user_turn.role == "user"
    assert user_turn.message == INBOUND_TEXT
    assert user_turn.timestamp

    # ---------------------------------------------------------
    # Assistant turn
    # ---------------------------------------------------------

    assistant_turn = turns[1]

    assert assistant_turn.role == "assistant"
    assert assistant_turn.message == EXPECTED_REPLY
    assert assistant_turn.timestamp

    print(" user turn       = PASS")
    print(" assistant turn  = PASS")

    # =========================================================
    # OUTBOUND ACTIVITY
    # =========================================================

    outbound = frappe.db.get_all(
        "Heshly WhatsApp Activity",
        filters={
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
            "direction": "outbound",
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
    )

    print()
    print("OUTBOUND ACTIVITIES")

    for row in outbound:
        print(row)

    assert len(outbound) == 1

    outbound_activity = outbound[0]

    assert outbound_activity.tenant_id == TENANT_ID
    assert outbound_activity.business_id == BUSINESS_ID
    assert outbound_activity.related_type == "WhatsApp Conversation"
    assert outbound_activity.related_id == RELATED_ID
    assert outbound_activity.direction == "outbound"
    assert outbound_activity.phone_number == PHONE
    assert outbound_activity.message == EXPECTED_REPLY

    # Real outbound send succeeded and the resulting
    # outbound activity was persisted.
    assert outbound_activity.status == "sent"

    assert outbound_activity.message_id
    assert outbound_activity.message_id != MESSAGE_ID

    print(" outbound activity = PASS")
    print(" outbound send failure persisted = PASS")

    # =========================================================
    # TOTAL ACTIVITY COUNT
    # =========================================================

    total = frappe.db.count(
        "Heshly WhatsApp Activity",
        {
            "tenant_id": TENANT_ID,
            "related_id": RELATED_ID,
        },
    )

    print()
    print("TOTAL CONVERSATION ACTIVITIES =", total)

    assert total == 2

    print(" activity count = PASS")

    # =========================================================
    # TENANT ISOLATION
    # =========================================================

    wrong_tenant_conversation = frappe.db.get_value(
        "AI Conversation",
        {
            "conversation_id": CONVERSATION_ID,
            "tenant_id": ["!=", TENANT_ID],
        },
        "name",
    )

    wrong_tenant_activity = frappe.db.get_value(
        "Heshly WhatsApp Activity",
        {
            "message_id": MESSAGE_ID,
            "tenant_id": ["!=", TENANT_ID],
        },
        "name",
    )

    assert wrong_tenant_conversation is None
    assert wrong_tenant_activity is None

    print(" tenant isolation = PASS")

    # =========================================================
    # FINAL
    # =========================================================

    print()
    print("=" * 80)
    print("REAL INBOUND WHATSAPP AI FLOW E2E PASSED")
    print("=" * 80)
    print()
    print("webhook entrypoint       = PASS")
    print("tenant resolution        = PASS")
    print("business mapping         = PASS")
    print("incoming message         = PASS")
    print("AI orchestration         = PASS")
    print("AI response              = PASS")
    print("AI conversation          = PASS")
    print("user turn persistence    = PASS")
    print("assistant turn           = PASS")
    print("inbound activity         = PASS")
    print("outbound activity        = PASS")
    print("tenant isolation         = PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()
