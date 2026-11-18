import frappe

from heshly_core.models.conversation import (
    ConversationStatus,
)
from heshly_core.services.conversation.conversation_manager import (
    ConversationManager,
)
from heshly_core.services.conversation.conversation_store import (
    ConversationStore,
)
from heshly_core.repositories.conversation_repository import (
    ConversationRepository,
)


TENANT_ID = "heshly"
CONVERSATION_ID = "PERSISTENCE-TEST-001"
CUSTOMER_ID = "254700000099"


def main():

    print("=" * 80)
    print("CONVERSATION PERSISTENCE INTEGRATION TEST")
    print("=" * 80)

    # ---------------------------------------------------------
    # CLEAN
    # ---------------------------------------------------------

    existing = frappe.db.get_value(
        "AI Conversation",
        {
            "conversation_id": CONVERSATION_ID,
            "tenant_id": TENANT_ID,
        },
        "name",
    )

    if existing:
        frappe.delete_doc(
            "AI Conversation",
            existing,
            ignore_permissions=True,
        )
        frappe.db.commit()

    # ---------------------------------------------------------
    # MANAGER -> STORE -> REPOSITORY
    # ---------------------------------------------------------

    manager = ConversationManager(
        tenant_id=TENANT_ID,
        channel="whatsapp",
    )

    conversation = manager.create(
        conversation_id=CONVERSATION_ID,
        customer_id=CUSTOMER_ID,
    )

    manager.add_user_message(
        conversation,
        "I want to book an appointment.",
    )

    manager.add_assistant_message(
        conversation,
        "Sure, what service would you like?",
    )

    manager.save(conversation)

    print()
    print("CREATED THROUGH MANAGER")
    print(" conversation_id =", conversation.conversation_id)
    print(" customer_id     =", conversation.customer_id)
    print(" status           =", conversation.status)
    print(" turn_count       =", conversation.turn_count())

    assert conversation.conversation_id == CONVERSATION_ID
    assert conversation.customer_id == CUSTOMER_ID
    assert conversation.turn_count() == 2

    # ---------------------------------------------------------
    # DIRECT DATABASE VERIFICATION
    # ---------------------------------------------------------

    print()
    print("DIRECT DATABASE VERIFICATION")

    db_row = frappe.db.get_value(
        "AI Conversation",
        {
            "conversation_id": CONVERSATION_ID,
            "tenant_id": TENANT_ID,
        },
        [
            "name",
            "conversation_id",
            "tenant_id",
            "customer_id",
            "channel",
            "status",
            "turn_count",
        ],
        as_dict=True,
    )

    print(" db_row =", db_row)

    assert db_row is not None
    assert db_row.conversation_id == CONVERSATION_ID
    assert db_row.tenant_id == TENANT_ID
    assert db_row.customer_id == CUSTOMER_ID
    assert db_row.channel == "whatsapp"
    assert db_row.status == ConversationStatus.ACTIVE.value
    assert int(db_row.turn_count) == 2

    # ---------------------------------------------------------
    # CHILD TABLE VERIFICATION
    # ---------------------------------------------------------

    doc = frappe.get_doc(
        "AI Conversation",
        db_row.name,
    )

    print()
    print("CHILD TURN TABLE")

    print(" turns =", len(doc.turns))

    for index, row in enumerate(doc.turns, start=1):
        print(
            f" turn {index}: "
            f"role={row.role!r}, "
            f"message={row.message!r}"
        )

    assert len(doc.turns) == 2

    assert doc.turns[0].role == "user"
    assert doc.turns[0].message == (
        "I want to book an appointment."
    )

    assert doc.turns[1].role == "assistant"
    assert doc.turns[1].message == (
        "Sure, what service would you like?"
    )

    # ---------------------------------------------------------
    # FRESH REPOSITORY READ
    # ---------------------------------------------------------

    print()
    print("FRESH REPOSITORY READ")

    repository = ConversationRepository()

    restored = repository.get(
        CONVERSATION_ID,
        tenant_id=TENANT_ID,
    )

    print(" restored conversation =", restored)
    print(" restored turns       =", len(restored.turns))

    assert restored is not None
    assert restored.conversation_id == CONVERSATION_ID
    assert restored.customer_id == CUSTOMER_ID
    assert restored.turn_count() == 2

    assert restored.turns[0].role.value == "user"
    assert restored.turns[0].message == (
        "I want to book an appointment."
    )

    assert restored.turns[1].role.value == "assistant"
    assert restored.turns[1].message == (
        "Sure, what service would you like?"
    )

    # ---------------------------------------------------------
    # MANAGER GET
    # ---------------------------------------------------------

    print()
    print("FRESH MANAGER READ")

    fresh_manager = ConversationManager(
        tenant_id=TENANT_ID,
        channel="whatsapp",
    )

    restored_again = fresh_manager.get(
        CONVERSATION_ID,
    )

    print(
        " restored_again =",
        restored_again,
    )

    assert restored_again is not None
    assert restored_again.conversation_id == CONVERSATION_ID
    assert restored_again.customer_id == CUSTOMER_ID
    assert restored_again.turn_count() == 2

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("CONVERSATION PERSISTENCE PASSED")
    print("=" * 80)

    print("ConversationManager")
    print("      -> ConversationStore")
    print("      -> ConversationRepository")
    print("      -> AI Conversation DocType")
    print("      -> MariaDB")
    print("      -> fresh repository read")
    print("      -> fresh manager read")
    print()
    print("Tenant:", TENANT_ID)
    print("Conversation:", CONVERSATION_ID)
    print("Turns persisted:", len(restored.turns))
    print("=" * 80)


if __name__ == "__main__":
    main()
