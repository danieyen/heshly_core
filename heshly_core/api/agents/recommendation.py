"""Recommendation specialist — ranking/explanation. Currently thin wrapper over matching (no extra ranking beyond Frappe)."""
from __future__ import annotations
import frappe
from heshly_core.api.agents.contracts import validate

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    candidates = kwargs.get("candidates") or []
    if candidates and isinstance(candidates, list):
        chosen = candidates[0]
        reason = "top_ranked_by_matching"
    else:
        chosen = None
        reason = "no_candidates"
    out = {"candidates": candidates, "chosen": chosen, "reason": reason}
    ok, err = validate("recommendation", out)
    if not ok:
        out["error"] = err
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "recommendation"}
