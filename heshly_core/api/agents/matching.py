"""Matching specialist — grounded retrieval from Heshly DB. Wraps offer_next_for_task only when should_search_providers."""
from __future__ import annotations
import json
import frappe
from heshly_core.services.network.consultation_engine import should_search_providers
from heshly_core.services.network.dispatch_service import offer_next_for_task
from heshly_core.api.agents.contracts import validate

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    # Called only when qualification done and location present
    network_conversation_id = kwargs.get("network_conversation_id") or kwargs.get("conversation_id") or ""
    task_id = kwargs.get("task_id")
    # If not provided, resolve from session/phone
    if not network_conversation_id and kwargs.get("session_id"):
        try:
            from heshly_core.api.website_chat import _phone_for_web_session, _normalize_web_session_id
            from heshly_core.services.network.network_conversation_service import get_or_create_conversation
            ch = kwargs.get("channel") or "web"
            phone = kwargs.get("phone") or kwargs.get("phone_number")
            if ch == "whatsapp" and phone:
                phone_norm = str(phone).strip()
            else:
                sid = _normalize_web_session_id(kwargs.get("session_id"))
                phone_norm = _phone_for_web_session(sid)
            conv = get_or_create_conversation(customer_phone=phone_norm, channel=ch)
            network_conversation_id = getattr(conv, "network_conversation_id", "") or ""
            if not task_id:
                # take active task
                qd = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                from heshly_core.services.network.consultation_engine import _load_tasks, get_active_task
                tasks = _load_tasks(qd) if isinstance(qd, dict) else []
                at = None
                for t in tasks:
                    if t.task_id == task_id:
                        at = t; break
                if not at:
                    # fallback: last task
                    at = tasks[-1] if tasks else None
                task_id = getattr(at, "task_id", None) if at else None
        except Exception:
            pass
    if not network_conversation_id:
        return {"candidates": [], "chosen": None, "reason": "no_conversation"}
    try:
        disp = offer_next_for_task(str(network_conversation_id), task_id)
        if disp:
            cand = {"business_id": getattr(disp, "business_id", ""), "score": getattr(disp, "ranking_score", 0)}
            out = {"candidates": [cand], "chosen": cand, "reason": "offer_next_for_task"}
        else:
            out = {"candidates": [], "chosen": None, "reason": "no_offer"}
    except Exception as e:
        out = {"candidates": [], "chosen": None, "reason": f"error:{e}"}
    ok, err = validate("recommendation", out)
    if not ok:
        out["error"] = err
    return out

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "matching"}
