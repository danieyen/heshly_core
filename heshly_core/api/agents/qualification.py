"""Qualification specialist — wraps qualify_message + consultation upsert/next question.
Does NOT overwrite unrelated state; owns only qualification_data supplement via orchestrator.
This specialist is called only when orchestrator determines more info is needed.
"""
from __future__ import annotations
import json, uuid
import frappe
from heshly_core.services.network.qualification_service import qualify_message
from heshly_core.services.network.consultation_engine import upsert_task_from_message, next_consultation_step, _load_tasks, _save_tasks
from heshly_core.services.network.network_conversation_service import get_or_create_conversation, append_turn, set_qualification
from heshly_core.api.agents.contracts import validate

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    text = (kwargs.get("text") or kwargs.get("current_message") or kwargs.get("message") or "").strip()
    session_id = kwargs.get("session_id") or ""
    channel = kwargs.get("channel") or "web"
    phone = kwargs.get("phone") or kwargs.get("phone_number") or ""
    tenant_id = kwargs.get("tenant_id")
    business_id = kwargs.get("business_id")
    # Load conversation (read-only qualification here; orchestrator owns persistence)
    from heshly_core.api.website_chat import _phone_for_web_session, _normalize_web_session_id
    if channel == "whatsapp" and phone:
        phone_norm = str(phone).strip()
        ch = "whatsapp"
    else:
        sid = _normalize_web_session_id(session_id) if session_id else _normalize_web_session_id(None)
        phone_norm = _phone_for_web_session(sid)
        ch = "web"
    try:
        conv = get_or_create_conversation(customer_phone=phone_norm, customer_name=kwargs.get("customer_name") or "Customer", source_phone_number_id=kwargs.get("phone_number_id"), channel=ch)
        existing = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
        if not isinstance(existing, dict):
            existing = {}
    except Exception:
        existing = {}
        conv = None
    qualified = qualify_message(text, existing if existing.get("consult_tasks") else existing)
    ex = {"requested_service": qualified.get("requested_service") or "", "location": qualified.get("location") or "", "raw_request": text}
    ct, _, new_qd = upsert_task_from_message(text, qualified if isinstance(qualified, dict) else {}, ex)
    q, _ = next_consultation_step(ct) if ct else (None, None)
    if ct and q:
        try:
            tasks = _load_tasks(new_qd)
            for t in tasks:
                if t.task_id == ct.task_id:
                    t.facts = dict(ct.facts)
                    t.matching_brief = ct.matching_brief or t.matching_brief
                    break
            new_qd = _save_tasks(new_qd, tasks)
        except Exception:
            pass
    collected = {"service": ex["requested_service"], "location": ex["location"], "raw_request": text}
    missing = []
    if not collected["service"]:
        missing.append("service")
    if not collected["location"]:
        missing.append("location")
    done = q is None
    out = {"collected": collected, "missing": missing, "done": done, "next_question": q, "qualified": qualified, "new_qd": new_qd}
    ok, err = validate("qualification", {"collected": collected, "missing": missing, "done": done, "next_question": q})
    if not ok:
        out["error"] = err
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "qualification"}
