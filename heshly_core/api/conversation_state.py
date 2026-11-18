from __future__ import annotations
from typing import Any

try:
    import frappe
except ImportError:
    class _MockWhitelist:
        def __call__(self, *a, **k):
            def decorator(fn): return fn
            return decorator
    class _MockFrappe:
        whitelist = _MockWhitelist()
    frappe = _MockFrappe()  # type: ignore

from heshly_core.services.conversation.conversation_state import build_conversation_state


def _parse(data: Any) -> dict:
    if isinstance(data, str):
        import json
        try:
            return json.loads(data)
        except Exception:
            return {}
    if isinstance(data, dict):
        return data
    return {}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def get_state(payload: Any = None, **kwargs: Any) -> dict:
    """
    Returns authoritative conversation_state derived from history + current message.
    Input: { turns: [...], message: {text: ...} or string, business_knowledge: {}, timezone }
    """
    data = _parse(payload) if payload is not None else {}
    # merge kwargs
    for k, v in (kwargs or {}).items():
        if k not in data or data[k] is None:
            data[k] = v
    # unwrap n8n wrappers
    for key in ("body", "data", "$json", "json"):
        if key in data and isinstance(data[key], dict) and ("turns" in data[key] or "message" in data[key]):
            data = data[key]
            break
    turns = data.get("turns") or data.get("conversation_history") or []
    msg = data.get("message")
    if isinstance(msg, dict):
        msg_text = msg.get("text") or msg.get("body") or msg.get("message") or ""
    else:
        msg_text = str(msg or data.get("current_message") or "")
    bk = data.get("business_knowledge") or data.get("knowledge") or {}
    # handle knowledge nested {knowledge: {...}}
    if isinstance(bk, dict) and "knowledge" in bk and isinstance(bk["knowledge"], dict):
        bk = bk["knowledge"]
    tz = data.get("timezone") or (bk.get("business", {}) or {}).get("timezone") or "Africa/Nairobi"
    # Try to parse explicit history format
    if isinstance(turns, str):
        import json
        try:
            turns = json.loads(turns)
        except Exception:
            turns = []
    if not isinstance(turns, list):
        turns = []
    state = build_conversation_state(turns, msg_text, bk, tz)
    return {"success": True, "state": state, "timezone": tz}
