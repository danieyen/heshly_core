import frappe


@frappe.whitelist(allow_guest=True, methods=["POST"])
def save_conversation_turn(
    conversation_id,
    tenant_id,
    intent,
    confidence,
    response,
    next_action,
):
    """
    Append an assistant AI turn to an existing AI Conversation.
    """

    if not conversation_id:
        frappe.throw("conversation_id is required")

    if not tenant_id:
        frappe.throw("tenant_id is required")

    if not response:
        frappe.throw("response is required")

    # ---------------------------------------------------------
    # Find conversation within tenant
    # ---------------------------------------------------------

    conversation_name = frappe.db.get_value(
        "AI Conversation",
        {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
        },
        "name",
    )

    if not conversation_name:
        frappe.throw(
            f"AI Conversation not found: {conversation_id}"
        )

    conversation = frappe.get_doc(
        "AI Conversation",
        conversation_name,
    )

    # ---------------------------------------------------------
    # Append assistant turn
    # ---------------------------------------------------------

    turn = conversation.append(
        "turns",
        {},
    )

    turn.role = "assistant"
    turn.message = response
    turn.intent = intent
    turn.confidence = float(confidence)
    turn.action = next_action
    turn.timestamp = frappe.utils.now_datetime()

    # ---------------------------------------------------------
    # Update conversation metadata
    # ---------------------------------------------------------

    conversation.intent = intent

    conversation.turn_count = len(
        conversation.turns
    )

    conversation.last_message_at = (
        turn.timestamp
    )

    # ---------------------------------------------------------
    # Persist
    # ---------------------------------------------------------

    conversation.flags.ignore_permissions = True

    conversation.save(
        ignore_permissions=True
    )

    frappe.db.commit()

    return {
        "success": True,
        "conversation_id": conversation.conversation_id,
        "turn_count": conversation.turn_count,
        "turn": {
            "role": turn.role,
            "message": turn.message,
            "intent": turn.intent,
            "confidence": turn.confidence,
            "action": turn.action,
            "timestamp": turn.timestamp,
        },
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def record_response_metrics(
    conversation_id,
    tenant_id,
    response_time_ms=None,
    response_status="success",
    token_usage=None,
    error_status=None,
):
    if not conversation_id:
        frappe.throw("conversation_id is required")

    if not tenant_id:
        frappe.throw("tenant_id is required")

    conversation_name = frappe.db.get_value(
        "AI Conversation",
        {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
        },
        "name",
    )

    if not conversation_name:
        frappe.throw(
            f"AI Conversation not found: {conversation_id}"
        )

    conversation = frappe.get_doc(
        "AI Conversation",
        conversation_name,
    )

    assistant_turn = None

    for turn in reversed(conversation.turns or []):
        if turn.role == "assistant":
            assistant_turn = turn
            break

    if assistant_turn is None:
        frappe.throw(
            f"No assistant turn found for conversation: {conversation_id}"
        )

    if response_time_ms not in (None, ""):
        assistant_turn.custom_response_time_ms = int(float(response_time_ms))

    if response_status not in (None, ""):
        assistant_turn.custom_response_status = str(response_status)

    if token_usage not in (None, ""):
        if isinstance(token_usage, dict):
            total_tokens = (
                token_usage.get("total_tokens")
                or token_usage.get("total")
                or token_usage.get("tokens")
            )
        else:
            total_tokens = token_usage

        if total_tokens not in (None, ""):
            assistant_turn.custom_token_usage = int(float(total_tokens))

    if error_status not in (None, ""):
        assistant_turn.custom_error_status = str(error_status)

    conversation.flags.ignore_permissions = True
    conversation.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "conversation_id": conversation_id,
        "tenant_id": tenant_id,
        "turn_name": assistant_turn.name,
        "response_time_ms": assistant_turn.custom_response_time_ms,
        "response_status": assistant_turn.custom_response_status,
        "token_usage": assistant_turn.custom_token_usage,
        "error_status": assistant_turn.custom_error_status,
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def record_conversation_outcome(
    conversation_id,
    tenant_id,
    outcome,
    completed=False,
    appointment_booked=False,
):
    if not conversation_id:
        frappe.throw("conversation_id is required")

    if not tenant_id:
        frappe.throw("tenant_id is required")

    if not outcome:
        frappe.throw("outcome is required")

    conversation_name = frappe.db.get_value(
        "AI Conversation",
        {
            "conversation_id": conversation_id,
            "tenant_id": tenant_id,
        },
        "name",
    )

    if not conversation_name:
        frappe.throw(
            f"AI Conversation not found: {conversation_id}"
        )

    conversation = frappe.get_doc(
        "AI Conversation",
        conversation_name,
    )

    conversation.flags.ignore_permissions = True

    if hasattr(conversation, "custom_outcome"):
        conversation.custom_outcome = outcome

    if hasattr(conversation, "custom_completed"):
        conversation.custom_completed = int(bool(completed))

    if hasattr(conversation, "custom_appointment_booked"):
        conversation.custom_appointment_booked = int(bool(appointment_booked))

    conversation.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "conversation_id": conversation_id,
        "tenant_id": tenant_id,
        "outcome": outcome,
        "completed": bool(completed),
        "appointment_booked": bool(appointment_booked),
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def update_ai_analytics(
    tenant_id,
    conversation_id=None,
    customer_id=None,
    lead_id=None,
    intent=None,
    intent_confidence=None,
    ai_response=None,
    next_action=None,
    appointment_booked=False,
    conversion_outcome=None,
    timestamp=None,
):
    if not tenant_id:
        frappe.throw("tenant_id is required")

    # Ensure the conversation belongs to this tenant when supplied.
    if conversation_id:
        exists = frappe.db.exists(
            "AI Conversation",
            {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
            },
        )

        if not exists:
            frappe.throw(
                f"AI Conversation not found: {conversation_id}"
            )

    # Store tenant-level aggregate counters in a simple cache-backed
    # structure for the dashboard.
    key = f"heshly_ai_analytics:{tenant_id}"

    analytics = frappe.cache().get_value(key) or {
        "total_interactions": 0,
        "successful_interactions": 0,
        "failed_interactions": 0,
        "appointments_booked": 0,
        "conversions": 0,
        "handover_count": 0,
    }

    analytics["total_interactions"] += 1
    analytics["successful_interactions"] += 1

    if appointment_booked:
        analytics["appointments_booked"] += 1

    if conversion_outcome:
        analytics["conversions"] += 1

    frappe.cache().set_value(
        key,
        analytics,
    )

    return {
        "success": True,
        "tenant_id": tenant_id,
        "conversation_id": conversation_id,
        "analytics": analytics,
    }


@frappe.whitelist(allow_guest=True)
def get_business_knowledge(tenant_id):
    if not tenant_id:
        frappe.throw("tenant_id is required")

    from heshly_core.services.ai.tenant_ai_manager import TenantAIManager

    manager = TenantAIManager()
    knowledge = manager.knowledge_context(tenant_id)

    if knowledge is None:
        return {
            "success": True,
            "tenant_id": tenant_id,
            "knowledge": {},
        }

    return {
        "success": True,
        "tenant_id": tenant_id,
        "knowledge": {
            "business": (
                {
                    "business_name": knowledge.business.business_name,
                    "industry": knowledge.business.industry,
                    "description": knowledge.business.description,
                    "timezone": knowledge.business.timezone,
                    "currency": knowledge.business.currency,
                }
                if knowledge.business else None
            ),
            "services": [
                {
                    "name": service.name,
                    "description": service.description,
                    "duration_minutes": service.duration_minutes,
                    "price": service.price,
                    "active": service.active,
                }
                for service in knowledge.services
            ],
            "products": knowledge.products,
            "staff": [],
            "faqs": [
                {
                    "question": faq.question,
                    "answer": faq.answer,
                }
                for faq in knowledge.faqs
            ],
            "policies": [
                {
                    "key": policy.key,
                    "value": policy.value,
                }
                for policy in knowledge.policies
            ],
        },
    }


