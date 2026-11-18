import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


def _tenant() -> str:
    return TenantContext().require()


def _defaults(tenant_id: str) -> dict:
    return {
        "tenant_id": tenant_id,
        "ai_enabled": 1,
        "personality": "Friendly & professional",
        "qualification_enabled": 1,
        "automatic_booking_enabled": 1,
        "human_escalation_enabled": 1,
        "prompt_protection_enabled": 1,
        "sensitive_data_protection_enabled": 1,
        "hallucination_detection_enabled": 1,
        "business_policy_enforcement_enabled": 1,
    }


def _get_or_create(tenant_id: str):
    name = frappe.db.get_value(
        "AI Configuration",
        {"tenant_id": tenant_id},
        "name",
    )

    if name:
        return frappe.get_doc("AI Configuration", name)

    doc = frappe.get_doc(
        {
            "doctype": "AI Configuration",
            **_defaults(tenant_id),
        }
    )

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return doc


def _serialize(doc) -> dict:
    return {
        "tenant_id": doc.tenant_id,
        "ai_enabled": bool(doc.ai_enabled),
        "personality": doc.personality,
        "qualification_enabled": bool(doc.qualification_enabled),
        "automatic_booking_enabled": bool(doc.automatic_booking_enabled),
        "human_escalation_enabled": bool(doc.human_escalation_enabled),
        "prompt_protection_enabled": bool(doc.prompt_protection_enabled),
        "sensitive_data_protection_enabled": bool(
            doc.sensitive_data_protection_enabled
        ),
        "hallucination_detection_enabled": bool(
            doc.hallucination_detection_enabled
        ),
        "business_policy_enforcement_enabled": bool(
            doc.business_policy_enforcement_enabled
        ),
    }


def _to_bool(value):
    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, int):
        return 1 if value else 0

    normalized = str(value).strip().lower()

    if normalized in ("1", "true", "yes", "on"):
        return 1

    if normalized in ("0", "false", "no", "off"):
        return 0

    raise ValueError(f"Invalid boolean value: {value}")


@frappe.whitelist()
def get_ai_config():
    tenant_id = _tenant()
    doc = _get_or_create(tenant_id)
    return _serialize(doc)


@frappe.whitelist(methods=["POST"])
def update_ai_config(
    ai_enabled=None,
    personality=None,
    qualification_enabled=None,
    automatic_booking_enabled=None,
    human_escalation_enabled=None,
    prompt_protection_enabled=None,
    sensitive_data_protection_enabled=None,
    hallucination_detection_enabled=None,
    business_policy_enforcement_enabled=None,
):
    tenant_id = _tenant()
    doc = _get_or_create(tenant_id)

    values = {
        "ai_enabled": ai_enabled,
        "personality": personality,
        "qualification_enabled": qualification_enabled,
        "automatic_booking_enabled": automatic_booking_enabled,
        "human_escalation_enabled": human_escalation_enabled,
        "prompt_protection_enabled": prompt_protection_enabled,
        "sensitive_data_protection_enabled": sensitive_data_protection_enabled,
        "hallucination_detection_enabled": hallucination_detection_enabled,
        "business_policy_enforcement_enabled": (
            business_policy_enforcement_enabled
        ),
    }

    for fieldname, value in values.items():
        if value is None:
            continue

        if fieldname.endswith("_enabled"):
            value = _to_bool(value)

        setattr(doc, fieldname, value)

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return _serialize(doc)

@frappe.whitelist(methods=["POST"])
def test_ai(message: str):
    """
    Test the tenant AI receptionist decision pipeline.

    Runs the deterministic DecisionEngine without creating
    a real conversation, appointment, or sending a message.
    """

    from heshly_core.services.ai.decision_engine import DecisionEngine

    message = (message or "").strip()

    if not message:
        frappe.throw("Message is required.")

    engine = DecisionEngine()
    context = engine.process(message)

    return {
        "message": message,

        "intent": {
            "value": (
                context.intent.intent.value
                if context.intent and context.intent.intent
                else None
            ),
            "confidence": (
                context.intent.confidence
                if context.intent
                else None
            ),
            "reasoning": (
                context.intent.reasoning
                if context.intent
                else None
            ),
        },

        "entities": {
            "service": (
                context.entities.service
                if context.entities
                else None
            ),
            "date": (
                context.entities.date
                if context.entities
                else None
            ),
            "time": (
                context.entities.time
                if context.entities
                else None
            ),
            "customer_name": (
                context.entities.customer_name
                if context.entities
                else None
            ),
            "phone": (
                context.entities.phone
                if context.entities
                else None
            ),
            "email": (
                context.entities.email
                if context.entities
                else None
            ),
        },

        "completeness": {
            "complete": (
                context.completeness.complete
                if context.completeness
                else False
            ),
            "missing_fields": (
                context.completeness.missing_fields
                if context.completeness
                else []
            ),
        },

        "rules": {
            "allowed": (
                context.rules.allowed
                if context.rules
                else None
            ),
            "reason": (
                context.rules.reason
                if context.rules
                else None
            ),
        },

        "action": {
            "value": (
                context.action.action.value
                if context.action
                else None
            ),
            "reason": (
                context.action.reason
                if context.action
                else None
            ),
        },
    }
