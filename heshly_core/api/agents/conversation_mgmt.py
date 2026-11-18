"""Conversation Management specialist — coordinates history/lifecycle.
Authoritative store remains Frappe Heshly Network Conversation (qualification_data + turns).
This module only reads/appends via network_conversation_service; it never creates a competing DB.
"""
from __future__ import annotations
import json
import frappe
from heshly_core.services.network.network_conversation_service import get_or_create_conversation, append_turn

@frappe.whitelist(allow_guest=True)
def handle(**kwargs):
    action = (kwargs.get("action") or "get_history").strip().lower()
    session_id = kwargs.get("session_id") or ""
    phone = kwargs.get("phone") or kwargs.get("phone_number") or ""
    channel = kwargs.get("channel") or "web"
    from heshly_core.api.website_chat import _phone_for_web_session, _normalize_web_session_id
    if channel == "whatsapp" and phone:
        phone_norm = str(phone).strip()
        ch = "whatsapp"
    else:
        sid = _normalize_web_session_id(session_id) if session_id else _normalize_web_session_id(None)
        phone_norm = _phone_for_web_session(sid)
        ch = "web"
    conv = get_or_create_conversation(customer_phone=phone_norm, channel=ch)
    if action == "append":
        role = kwargs.get("role") or "assistant"
        message = kwargs.get("message") or kwargs.get("text") or ""
        if message:
            append_turn(conv, role, message)
        return {"success": True, "appended": True, "turn_count": int(getattr(conv, "turn_count", 0) or 0)}
    # get_history
    turns = []
    for t in (getattr(conv, "turns", []) or [])[-20:]:
        turns.append({"role": getattr(t, "role", ""), "message": getattr(t, "message", ""), "timestamp": str(getattr(t, "timestamp", "") or "")})
    return {"success": True, "turns": turns, "turn_count": int(getattr(conv, "turn_count", 0) or 0), "network_conversation_id": getattr(conv, "network_conversation_id", "")}

@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "agent": "conversation_mgmt"}
