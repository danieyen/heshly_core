"""Reception specialist — greetings, acknowledgements. No matching. Owned state: none (read-only)."""
from __future__ import annotations
import frappe
from heshly_core.api.agents.contracts import validate

GREETINGS = {"hi","hello","hey","habari","mambo","good morning","good afternoon","good evening"}

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    text = (kwargs.get("text") or kwargs.get("current_message") or kwargs.get("message") or "").strip()
    low = text.lower().strip()
    is_greeting = low in GREETINGS or low.startswith("hi ") or low.startswith("hello") or low.startswith("hey ")
    if is_greeting:
        response = "Hello! How can I help you today?"
        intent = "GREETING"
    else:
        response = "Got it — how can I help today?"
        intent = "OTHER"
    out = {"response": response, "intent": intent, "domain": "general", "qualification_state": "pending", "delivery_status": "pending", "candidates": []}
    ok, err = validate("response", {"response": response})
    if not ok:
        out["response"] = "Hello! How can I help you today?"
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "reception"}
