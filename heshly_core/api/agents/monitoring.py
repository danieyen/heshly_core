"""Monitoring specialist — records failures/outcomes to Error Log. Never delivers to customer."""
from __future__ import annotations
import json
import frappe

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    level = kwargs.get("level") or "info"
    message = kwargs.get("message") or kwargs.get("error") or ""
    workflow_id = kwargs.get("workflow_id") or kwargs.get("workflowId") or ""
    execution_id = kwargs.get("execution_id") or ""
    if level in ("error", "failed") and message:
        try:
            frappe.log_error(str(message)[:5000], f"heshly-v2-monitoring {workflow_id} {execution_id}"[:140])
        except Exception:
            pass
    return {"success": True, "logged": True, "level": level}

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "monitoring"}
