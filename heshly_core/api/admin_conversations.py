from __future__ import annotations

import frappe


def _is_platform_admin() -> bool:
    """Allow only Heshly platform administrators to access all tenants."""
    user = frappe.session.user

    if user == "Administrator":
        return True

    try:
        if "System Manager" in frappe.get_roles(user):
            return True
    except Exception:
        pass

    # Heshly's own platform tenant
    try:
        business_id = frappe.session.data.get("heshly_business_id")

        if business_id == "HESHLY":
            role = frappe.db.get_value(
                "User Business Membership",
                {
                    "user": user,
                    "business_id": "HESHLY",
                    "tenant_id": "heshly",
                    "active": 1,
                },
                "role",
            )

            if role in ("Owner", "Administrator"):
                return True
    except Exception:
        pass

    return False


def _require_platform_admin():
    if not _is_platform_admin():
        frappe.throw(
            "Platform administrator access required.",
            frappe.PermissionError,
        )


def _business_name(business_id: str | None) -> str | None:
    if not business_id:
        return None

    try:
        return frappe.db.get_value(
            "Business Account",
            {"business_id": business_id},
            "business_name",
        ) or business_id
    except Exception:
        return business_id


def _business_for_tenant(tenant_id: str | None) -> dict:
    if not tenant_id:
        return {
            "business_id": None,
            "business_name": None,
        }

    try:
        row = frappe.db.get_value(
            "Business Account",
            {"tenant_id": tenant_id},
            ["business_id", "business_name"],
            as_dict=True,
        )

        if row:
            return {
                "business_id": row.get("business_id"),
                "business_name": row.get("business_name")
                    or row.get("business_id"),
            }
    except Exception:
        pass

    # Fallback for the canonical Heshly tenant
    if tenant_id == "heshly":
        return {
            "business_id": "HESHLY",
            "business_name": "Heshly Studio",
        }

    return {
        "business_id": None,
        "business_name": None,
    }


def _serialize_turn(row) -> dict:
    return {
        "role": row.role,
        "message": row.message,
        "intent": row.intent,
        "confidence": row.confidence,
        "action": row.action,
        "timestamp": row.timestamp,
    }


def _serialize_conversation(doc, include_turns: bool = False) -> dict:
    business = _business_for_tenant(doc.tenant_id)

    result = {
        "conversation_id": doc.conversation_id,
        "tenant_id": doc.tenant_id,
        "business_id": business.get("business_id"),
        "business_name": business.get("business_name"),
        "customer_id": doc.customer_id,
        "customer_name": doc.customer_name,
        "customer_phone": doc.customer_phone,
        "customer_email": doc.customer_email,
        "channel": doc.channel,
        "status": doc.status,
        "service": doc.service,
        "intent": doc.intent,
        "appointment_date": doc.appointment_date,
        "appointment_time": doc.appointment_time,
        "turn_count": doc.turn_count or 0,
        "started_at": doc.started_at,
        "last_message_at": doc.last_message_at,
    }

    if include_turns:
        turns = list(doc.turns or [])

        # Old records may not have timestamps. Frappe's child-table
        # order is the persistence order, so preserve it when timestamps
        # are unavailable.
        turns.sort(
            key=lambda row: (
                row.timestamp is None,
                row.timestamp or "",
                row.idx or 0,
            )
        )

        result["turns"] = [_serialize_turn(row) for row in turns]

    return result


@frappe.whitelist(allow_guest=False)
def list_conversations(
    limit: int = 200,
    offset: int = 0,
    status: str | None = None,
    tenant_id: str | None = None,
):
    """Platform-wide conversation list for the Heshly Admin dashboard."""
    _require_platform_admin()

    try:
        limit = max(1, min(int(limit), 500))
    except Exception:
        limit = 200

    try:
        offset = max(0, int(offset))
    except Exception:
        offset = 0

    filters = {}

    if status:
        filters["status"] = str(status).strip().lower()

    if tenant_id:
        filters["tenant_id"] = str(tenant_id).strip()

    conversations = frappe.get_all(
        "AI Conversation",
        filters=filters,
        fields=[
            "name",
            "conversation_id",
            "tenant_id",
            "customer_id",
            "customer_name",
            "customer_phone",
            "customer_email",
            "channel",
            "status",
            "service",
            "intent",
            "turn_count",
            "started_at",
            "last_message_at",
        ],
        order_by="last_message_at desc, modified desc",
        limit_start=offset,
        limit_page_length=limit,
        ignore_permissions=True,
    )

    result = []

    for row in conversations:
        business = _business_for_tenant(row.tenant_id)

        result.append({
            "conversation_id": row.conversation_id,
            "tenant_id": row.tenant_id,
            "business_id": business.get("business_id"),
            "business_name": business.get("business_name"),
            "customer_id": row.customer_id,
            "customer_name": row.customer_name,
            "customer_phone": row.customer_phone,
            "customer_email": row.customer_email,
            "channel": row.channel,
            "status": row.status,
            "service": row.service,
            "intent": row.intent,
            "turn_count": row.turn_count or 0,
            "started_at": row.started_at,
            "last_message_at": row.last_message_at,
        })

    total = frappe.db.count(
        "AI Conversation",
        filters=filters,
    )

    return {
        "success": True,
        "conversations": result,
        "count": len(result),
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@frappe.whitelist(allow_guest=False)
def get_conversation(conversation_id: str):
    """Return one complete conversation and its entire message history."""
    _require_platform_admin()

    if not conversation_id:
        frappe.throw("conversation_id is required")

    conversation_id = str(conversation_id).strip()

    name = frappe.db.get_value(
        "AI Conversation",
        {"conversation_id": conversation_id},
        "name",
    )

    if not name:
        frappe.throw("Conversation not found.", frappe.DoesNotExistError)

    doc = frappe.get_doc(
        "AI Conversation",
        name,
    )

    return {
        "success": True,
        "conversation": _serialize_conversation(
            doc,
            include_turns=True,
        ),
    }
