"""Dispatcher specialist — maps domain deterministically. Wraps _deterministic_domain."""
from __future__ import annotations
import frappe
from heshly_core.api.agents.orchestrator import _deterministic_domain
from heshly_core.api.agents.contracts import validate

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    text = (kwargs.get("text") or kwargs.get("current_message") or kwargs.get("message") or "").strip()
    requested = kwargs.get("requested_service") or kwargs.get("service") or ""
    out = _deterministic_domain(text, requested)
    ok, err = validate("domain", out)
    if not ok:
        out = {"domain": "general", "confidence": 0.5, "reason": "fallback"}
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "dispatcher"}
