"""Response specialist — final natural language. Validates RESPONSE_SCHEMA. Never echoes raw service name verbatim."""
from __future__ import annotations
import frappe
from heshly_core.api.agents.contracts import validate

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    response = kwargs.get("response") or kwargs.get("text") or kwargs.get("message") or ""
    if not response:
        response = "How can I help you today?"
    out = {"response": str(response)[:2000]}
    ok, err = validate("response", out)
    if not ok:
        out = {"response": "How can I help you today?", "error": err}
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "response"}
