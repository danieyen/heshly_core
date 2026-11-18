"""Strict JSON contracts for the orchestrator and all specialist agents.

Every agent must obey these schemas.  No agent may overwrite unrelated state.
The orchestrator validates every output before forwarding.
"""
from __future__ import annotations

ALLOWED_INTENTS = {
    "GREETING", "SERVICE_REQUEST", "TROUBLESHOOTING", "PRODUCT_SEARCH",
    "ADVICE", "CORRECTION", "DISSATISFACTION", "RESET", "OTHER"
}

ALLOWED_DOMAINS = {
    "plumbing", "electrical", "hvac", "pest_control", "cleaning", "general_repairs",
    "water_heater", "roofing", "painting", "tiling", "carpentry", "general"
}

INTENT_SCHEMA = {
    "type": "object",
    "required": ["intent", "confidence", "is_correction", "is_dissatisfaction"],
    "properties": {
        "intent": {"type": "string", "enum": sorted(ALLOWED_INTENTS)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "is_correction": {"type": "boolean"},
        "is_dissatisfaction": {"type": "boolean"},
        "raw_text": {"type": "string"},
        "entities": {"type": "object"},
    },
}

DOMAIN_SCHEMA = {
    "type": "object",
    "required": ["domain", "confidence"],
    "properties": {
        "domain": {"type": "string", "enum": sorted(ALLOWED_DOMAINS)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"},
    },
}

QUALIFICATION_SCHEMA = {
    "type": "object",
    "required": ["collected", "missing", "done"],
    "properties": {
        "collected": {"type": "object"},  # urgency, location, budget, service
        "missing": {"type": "array", "items": {"type": "string"}},
        "done": {"type": "boolean"},
        "next_question": {"type": ["string", "null"]},
    },
}

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "required": ["candidates", "chosen", "reason"],
    "properties": {
        "candidates": {"type": "array"},
        "chosen": {"type": ["object", "null"]},
        "reason": {"type": "string"},
    },
}

RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["response"],
    "properties": {
        "response": {"type": "string", "minLength": 1, "maxLength": 2000},
    },
}

ORCHESTRATOR_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["response", "intent", "domain", "qualification_state", "delivery_status"],
    "properties": {
        "response": {"type": "string"},
        "intent": {"type": "string"},
        "domain": {"type": "string"},
        "qualification_state": {"type": "string"},
        "delivery_status": {"type": "string", "enum": ["pending", "delivered", "failed", "retry"]},
        "candidates": {"type": "array"},
        "chosen_business_id": {"type": ["string", "null"]},
    },
}


def validate(schema_name: str, payload: dict) -> tuple[bool, str]:
    """Validate payload against named schema using lightweight checks."""
    schemas = {
        "intent": INTENT_SCHEMA,
        "domain": DOMAIN_SCHEMA,
        "qualification": QUALIFICATION_SCHEMA,
        "recommendation": RECOMMENDATION_SCHEMA,
        "response": RESPONSE_SCHEMA,
    }
    schema = schemas.get(schema_name)
    if not schema:
        return False, f"unknown schema {schema_name}"
    for req in schema.get("required", []):
        if req not in payload:
            return False, f"missing required field: {req}"
    # enum checks
    for field, prop in schema.get("properties", {}).items():
        if field in payload and "enum" in prop:
            if payload[field] not in prop["enum"]:
                return False, f"field {field} value {payload[field]!r} not in {prop['enum']}"
    return True, ""


# Shared conversation state — authoritative owner is Frappe network_conversation_service
SHARED_STATE_KEYS = {
    "session_id", "customer_id", "channel", "current_message", "message_id",
    "intent", "domain", "qualification", "missing", "stage",
    "last_response_id", "delivery_status", "tenant_id", "business_id"
}
