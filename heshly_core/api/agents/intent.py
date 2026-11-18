"""Intent specialist — identifies intent/correction/dissatisfaction. Uses same deterministic logic as orchestrator."""
from __future__ import annotations
import frappe
from heshly_core.api.agents.orchestrator import _deterministic_intent
from heshly_core.api.agents.contracts import validate

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    text = (kwargs.get("text") or kwargs.get("current_message") or kwargs.get("message") or "").strip()
    prev_service = kwargs.get("previous_service") or kwargs.get("prev_service") or ""
    out = _deterministic_intent(text, prev_service)
    ok, err = validate("intent", out)
    if not ok:
        out = {"intent": "OTHER", "confidence": 0.5, "is_correction": False, "is_dissatisfaction": False, "raw_text": text, "entities": {}}
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "intent"}
