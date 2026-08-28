import frappe

from heshly_core.services.conversation.conversation_manager import (
    ConversationManager,
)


def _manager():
    tenant_id = getattr(frappe.local, "heshly_tenant_id", None)

    if not tenant_id:
        tenant_id = "heshly"

    return ConversationManager(
        tenant_id=tenant_id,
        channel="whatsapp",
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
def create(
    conversation_id: str,
    customer_id: str,
    tenant_id: str | None = None,
):
    if tenant_id:
        from heshly_core.services.tenant.tenant_context import TenantContext
        TenantContext().set(tenant_id)

    manager = _manager()

    existing = manager.get(conversation_id)

    if existing:
        return {
            "conversation_id": existing.conversation_id,
            "customer_id": existing.customer_id,
            "status": existing.status.value,
            "turn_count": existing.turn_count(),
            "created": False,
        }

    conversation = manager.create(
        conversation_id=conversation_id,
        customer_id=customer_id,
    )

    return {
        "conversation_id": conversation.conversation_id,
        "customer_id": conversation.customer_id,
        "status": conversation.status.value,
        "turn_count": conversation.turn_count(),
        "created": True,
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def message(
    conversation_id: str,
    role: str,
    message: str,
):
    manager = _manager()

    conversation = manager.get(conversation_id)

    if conversation is None:
        frappe.throw(
            f"Conversation {conversation_id} not found",
            frappe.DoesNotExistError,
        )

    role = role.lower().strip()

    if role == "user":
        manager.add_user_message(
            conversation,
            message,
        )

    elif role == "assistant":
        manager.add_assistant_message(
            conversation,
            message,
        )

    elif role == "system":
        manager.add_system_message(
            conversation,
            message,
        )

    else:
        frappe.throw(
            "role must be user, assistant, or system"
        )

    manager.save(conversation)

    return {
        "conversation_id": conversation.conversation_id,
        "status": conversation.status.value,
        "turn_count": conversation.turn_count(),
        "message": message,
        "role": role,
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def get(
    conversation_id: str,
    tenant_id: str | None = None,
):
    if tenant_id:
        from heshly_core.services.tenant.tenant_context import TenantContext
        TenantContext().set(tenant_id)

    manager = _manager()

    conversation = manager.get(conversation_id)

    if conversation is None:
        frappe.throw(
            f"Conversation {conversation_id} not found",
            frappe.DoesNotExistError,
        )

    return {
        "conversation_id": conversation.conversation_id,
        "customer_id": conversation.customer_id,
        "status": conversation.status.value,
        "service": conversation.entities.service,
        "appointment_date": conversation.entities.date,
        "appointment_time": conversation.entities.time,
        "customer_name": conversation.entities.customer_name,
        "customer_phone": conversation.entities.phone,
        "customer_email": conversation.entities.email,
        "turn_count": conversation.turn_count(),
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "turns": [
            {
                "role": turn.role.value,
                "message": turn.message,
                "timestamp": turn.timestamp,
            }
            for turn in conversation.turns
        ],
    }


@frappe.whitelist()
def list():
    manager = _manager()

    conversations = manager.store.all()

    return {
        "count": len(conversations),
        "conversations": [
            {
                "conversation_id": conversation.conversation_id,
                "customer_id": conversation.customer_id,
                "status": conversation.status.value,
                "service": conversation.entities.service,
                "customer_name": conversation.entities.customer_name,
                "customer_phone": conversation.entities.phone,
                "turn_count": conversation.turn_count(),
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
            }
            for conversation in conversations
        ],
    }


@frappe.whitelist(methods=["POST"])
def close(conversation_id: str):
    manager = _manager()

    conversation = manager.get(conversation_id)

    if conversation is None:
        frappe.throw(
            f"Conversation {conversation_id} not found",
            frappe.DoesNotExistError,
        )

    manager.close(conversation)

    return {
        "conversation_id": conversation.conversation_id,
        "status": conversation.status.value,
    }


@frappe.whitelist(methods=["POST"])
def handover(conversation_id: str):
    manager = _manager()

    conversation = manager.get(conversation_id)

    if conversation is None:
        frappe.throw(
            f"Conversation {conversation_id} not found",
            frappe.DoesNotExistError,
        )

    manager.handover(conversation)

    return {
        "conversation_id": conversation.conversation_id,
        "status": conversation.status.value,
    }

@frappe.whitelist(allow_guest=True, methods=["POST"])
def find_or_create(
    customer_id: str,
    tenant_id: str,
):
    from heshly_core.services.tenant.tenant_context import TenantContext
    import uuid

    tenant_id = tenant_id.strip() if tenant_id else None
    customer_id = customer_id.strip() if customer_id else None

    if not tenant_id:
        frappe.throw("tenant_id is required")

    if not customer_id:
        frappe.throw("customer_id is required")

    TenantContext().set(tenant_id)

    manager = _manager()

    conversations = manager.store.all()

    for conversation in reversed(conversations):
        if conversation.customer_id == customer_id:
            return {
                "found": True,
                "created": False,
                "conversation_id": conversation.conversation_id,
                "customer_id": conversation.customer_id,
                "status": conversation.status.value,
                "turn_count": conversation.turn_count(),
            }

    conversation_id = f"CONV-{uuid.uuid4().hex[:12].upper()}"

    conversation = manager.create(
        conversation_id=conversation_id,
        customer_id=customer_id,
    )

    return {
        "found": False,
        "created": True,
        "conversation_id": conversation.conversation_id,
        "customer_id": conversation.customer_id,
        "status": conversation.status.value,
        "turn_count": conversation.turn_count(),
    }



@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def get_stale(hours=24, limit=50):

    cutoff = frappe.utils.add_to_date(
        frappe.utils.now_datetime(),
        hours=-int(hours),
    )

    conversations = frappe.get_all(
        "AI Conversation",
        filters={
            "status": "active",
            "last_message_at": ["<=", cutoff],
        },
        fields=[
            "name",
            "conversation_id",
            "tenant_id",
            "customer_id",
            "channel",
            "status",
            "service",
            "appointment_date",
            "appointment_time",
            "customer_name",
            "customer_phone",
            "customer_email",
            "intent",
            "turn_count",
            "started_at",
            "last_message_at",
        ],
        order_by="last_message_at asc",
        limit_page_length=int(limit),
    )

    return {
        "success": True,
        "count": len(conversations),
        "conversations": conversations,
    }


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def handle_stale(hours=24, limit=50):

    cutoff = frappe.utils.add_to_date(
        frappe.utils.now_datetime(),
        hours=-int(hours),
    )

    conversations = frappe.get_all(
        "AI Conversation",
        filters={
            "status": "active",
            "last_message_at": ["<=", cutoff],
        },
        fields=[
            "name",
            "conversation_id",
            "customer_id",
            "status",
            "last_message_at",
        ],
        order_by="last_message_at asc",
        limit_page_length=int(limit),
    )

    handled = []

    for conversation in conversations:

        frappe.db.set_value(
            "AI Conversation",
            conversation["name"],
            "status",
            "handover",
        )

        handled.append(conversation["conversation_id"])

    frappe.db.commit()

    return {
        "success": True,
        "count": len(handled),
        "handled": handled,
    }
