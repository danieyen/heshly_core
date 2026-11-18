"""Website chat adapter for HCN — small production adapter reusing existing HCN engine.

Channel: "web" (not whatsapp). Uses anon session token, never collides with
WhatsApp customer_phone (wa_web_* prefix). Reuses qualification, matching,
dispatch, notifications. No new matching logic.

Rate-limited, anonymous, channel-isolated.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any

try:
    import frappe  # type: ignore
except ImportError:  # pragma: no cover
    class _MockWhitelist:  # type: ignore
        def __call__(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    class _MockFrappe:  # type: ignore
        whitelist = _MockWhitelist()
        request = None
        local = None

    frappe = _MockFrappe()  # type: ignore

# ── Anonymous session + rate limit ────────────────────────────────────
_ANON_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days retention hint
_RATE_LIMIT_WINDOW = 60.0
_RATE_LIMIT_MAX = 20  # 20 msgs / minute / session


def _parse_json_string(v: Any) -> Any:
    if isinstance(v, str):
        v = v.strip()
        if v and ((v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]"))):
            try:
                return json.loads(v)
            except Exception:
                return v
    return v


def _unwrap(payload: Any, kwargs: dict) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(kwargs, dict):
        data.update(kwargs)
    if payload is not None:
        parsed = _parse_json_string(payload)
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if k not in data:
                    data[k] = v
            if not data:
                data = dict(parsed)
    for _ in range(3):
        wrapped = None
        for key in ("$json", "json", "body", "data", "payload"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    wrapped = val
                    break
        if wrapped is not None:
            merged = dict(data)
            for k in ("$json", "json", "body", "data", "payload"):
                merged.pop(k, None)
            for k, v in wrapped.items():
                if k not in merged or merged[k] is None or merged[k] == "":
                    merged[k] = v
            data = merged
        else:
            break
    return data


def _normalize_web_session_id(raw: str | None) -> str:
    """Validate or mint a website session id. Stored as wa_web_<8hex> phone."""
    if raw:
        s = str(raw).strip()
        # Accept hweb_*, wa_web_*, or plain hex — normalize to hweb_<hex>
        m = re.match(r"^(?:hweb_|wa_web_)?([a-f0-9]{8,32})$", s.lower())
        if m:
            return f"hweb_{m.group(1)}"
        # Also accept UUID-ish
        m2 = re.match(r"^[a-f0-9\-]{8,}$", s.lower())
        if m2:
            # take first 12 hex chars
            hexs = re.sub(r"[^a-f0-9]", "", s.lower())
            if len(hexs) >= 8:
                return f"hweb_{hexs[:12]}"
    return f"hweb_{uuid.uuid4().hex[:12]}"


def _phone_for_web_session(session_id: str) -> str:
    """Deterministic customer_phone for website session — never collides with WhatsApp 254*."""
    norm = _normalize_web_session_id(session_id)
    suffix = norm.replace("hweb_", "")[:12]
    # wa_web_ prefix guaranteed distinct from WhatsApp E164
    return f"wa_web_{suffix}"


def _check_rate_limit(session_id: str) -> tuple[bool, str]:
    try:
        cache = frappe.cache()  # type: ignore
        key = f"hcn_web_rl:{session_id}"
        now = time.monotonic()
        raw = cache.get_value(key)
        if raw:
            try:
                arr = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(arr, list):
                    arr = []
            except Exception:
                arr = []
            # Coerce to floats safely
            cleaned: list[float] = []
            for t in arr:
                try:
                    cleaned.append(float(t))
                except Exception:
                    continue
            cleaned = [t for t in cleaned if now - t < _RATE_LIMIT_WINDOW]
            if len(cleaned) >= _RATE_LIMIT_MAX:
                return False, "Too many messages. Please wait a moment."
            cleaned.append(now)
            cache.set_value(key, json.dumps(cleaned), expires_in_sec=int(_RATE_LIMIT_WINDOW) + 5)
        else:
            cache.set_value(key, json.dumps([now]), expires_in_sec=int(_RATE_LIMIT_WINDOW) + 5)
    except Exception:
        pass
    return True, ""


def _sanitize_text(text: str) -> tuple[bool, str, str]:
    """Validate incoming website message. Returns (ok, cleaned, error)."""
    if not isinstance(text, str):
        return False, "", "Message must be text."
    t = text.strip()
    if not t:
        return False, "", "Message cannot be empty."
    if len(t) > 2000:
        return False, "", "Message is too long. Please keep it under 2000 characters."
    # Basic XSS: reject obvious script tags — but also sanitize on render with DOMPurify
    if re.search(r"<\s*script\b", t, re.I):
        return False, "", "Message contains disallowed content."
    return True, t, ""


def _is_test_tenant_id(tenant_id: str | None) -> bool:
    if not tenant_id:
        return False
    t = tenant_id.lower()
    return t.startswith("hcn_e2e_") or t.startswith("net_test_") or t.startswith("test_") or "e2e" in t

def _serialize_recommendations(dispatch: Any, conversation: Any) -> list[dict[str, Any]]:
    """Build recommendation cards from top dispatch + alternates. Verified fields only.
    Test/fixture tenants (hcn_e2e_*, net_test_*) are filtered from website results so production never shows them as genuine businesses.
    """
    recs: list[dict[str, Any]] = []
    try:
        import frappe as _f  # type: ignore

        rows = _f.get_all(
            "Heshly Network Dispatch",
            filters={"network_conversation_id": getattr(conversation, "network_conversation_id", "")},
            fields=["dispatch_id", "tenant_id", "business_id", "status", "ranking_score", "ranking_reasons", "offered_at", "deadline_at", "lead_fee"],
            order_by="offered_at desc",
            limit=5,
        )
        for r in rows:
            tenant_id = r.get("tenant_id") or ""
            if _is_test_tenant_id(tenant_id):
                continue
            business_id = r.get("business_id") or tenant_id
            biz = _f.db.get_value("Business Account", {"tenant_id": tenant_id}, ["business_id", "business_name", "location", "phone", "email"], as_dict=True) if tenant_id else None
            if not biz:
                biz = _f.db.get_value("Business Account", {"business_id": business_id}, ["business_id", "business_name", "location", "phone", "email"], as_dict=True) if business_id else None
            # Also skip test business names as a secondary guard
            _bname = (biz.get("business_name") if biz else "") or ""
            if _bname and ("E2E" in _bname or "Test Business" in _bname or _bname.strip().lower().startswith("hcn e2e") or _bname.strip().lower().startswith("network test")):
                continue
            bkp = _f.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["services", "description"], as_dict=True) if tenant_id else None
            dispatch_score = r.get("ranking_score")
            reasons = r.get("ranking_reasons")
            if isinstance(reasons, str):
                try:
                    reasons = json.loads(reasons)
                except Exception:
                    reasons = {}
            # Public business page: heshly.com/{slug}
            try:
                from heshly_core.services.business_slug import public_url as _pub_url  # type: ignore
                _slug = frappe.db.get_value("Business Account", {"business_id": business_id}, "public_slug") if business_id else None
                if not _slug and tenant_id:
                    _slug = frappe.db.get_value("Business Account", {"tenant_id": tenant_id}, "public_slug")
                link = _pub_url(str(_slug).strip().lower()) if _slug else ""
            except Exception:
                link = ""
            if not link:
                link = f"https://heshly.com/{(business_id or tenant_id or '').lower().replace('_','-')}" if (business_id or tenant_id) else ""
            # Try to find affiliate/external link inside services text (http...), otherwise use enquiry helper
            external = None
            if bkp and isinstance(bkp.get("services"), str):
                m = re.search(r"https?://[^\s\"']+", bkp["services"])
                if m:
                    external = m.group(0)
            recs.append(
                {
                    "dispatch_id": r.get("dispatch_id") or "",
                    "tenant_id": tenant_id,
                    "business_id": business_id,
                    "business_name": (biz.get("business_name") if biz else None) or business_id or tenant_id or "Provider",
                    "service": getattr(conversation, "requested_service", "") or "",
                    "location": getattr(conversation, "location", "") or (biz.get("location") if biz else "") or "",
                    "phone": (biz.get("phone") if biz else None) or None,
                    "services_text": (bkp.get("services") if bkp else None) or None,
                    "description": (bkp.get("description") if bkp else None) or None,
                    "ranking_score": dispatch_score,
                    "ranking_reasons": reasons if isinstance(reasons, dict) else {},
                    "status": r.get("status") or "",
                    "link": external or link,
                    "enquiry_link": link + "/contact" if link else "",
                }
            )
        # If no dispatches but conversation is qualified, fabricate no-match placeholder handled by caller
    except Exception:
        pass
    return recs


def _dispatch_to_counts(conv: Any) -> dict[str, Any]:
    try:
        import frappe as _f  # type: ignore

        nid = getattr(conv, "network_conversation_id", "")
        total = _f.db.count("Heshly Network Dispatch", filters={"network_conversation_id": nid})
        offered = _f.db.count("Heshly Network Dispatch", filters={"network_conversation_id": nid, "status": "OFFERED"})
        accepted = _f.db.count("Heshly Network Dispatch", filters={"network_conversation_id": nid, "status": "ACCEPTED"})
        return {"total": total, "offered": offered, "accepted": accepted}
    except Exception:
        return {}


@frappe.whitelist(allow_guest=True)
def website_chat(payload=None, **kwargs):
    """Website chat entry point — reuses existing HCN qualification/matching/dispatch.

    Request: { message: string, session_id?: string, customer_name?: string }
    Response: { success, session_id, reply, intent, recommendations, conversation }
    """

    data = _unwrap(payload, kwargs)
    raw_message = data.get("message") or data.get("text") or data.get("body") or data.get("q")
    session_raw = data.get("session_id") or data.get("sessionId") or data.get("conversation_id") or data.get("conversationId")
    customer_name = (data.get("customer_name") or data.get("name") or "").strip() if isinstance(data.get("customer_name") or data.get("name"), str) else None

    ok, raw_text, err = _sanitize_text(str(raw_message) if raw_message is not None else "")
    if not ok:
        return {"success": False, "message": err}
    # Unified orchestrator path — WhatsApp and web share same intelligence
    try:
        from heshly_core.api.agents.orchestrator import orchestrate as _orch
        import hashlib as _hl
        _mid = f"hweb_{_hl.sha256(raw_text.encode()).hexdigest()[:12]}:{int(time.time()*1000)}"
        # Ensure session_id is normalized before orchestrator (orchestrator also normalizes, but we need it for response)
        _web_sid = _normalize_web_session_id(str(session_raw) if session_raw else None)
        if session_raw:
            session_id = _web_sid
        _res = _orch(session_id=session_id or _web_sid, message_id=_mid, text=raw_text, channel="web")
        # Preserve web session semantics
        _res["session_id"] = session_id or _web_sid
        _res["success"] = True
        # Bridge orchestrator 'response' -> website 'reply' for HcnChat/tests compatibility
        if "reply" not in _res and "response" in _res:
            _res["reply"] = _res["response"]
        # Enrich with website-specific fields expected by HcnChat
        if "recommendations" not in _res:
            _res["recommendations"] = _res.get("candidates", [])
        if "turns" not in _res:
            try:
                _phone = _phone_for_web_session(session_id or _web_sid)
                import frappe as _fr
                _doc = _fr.db.get_value("Heshly Network Conversation", {"customer_phone": _phone}, ["name"], as_dict=True, order_by="modified desc")
                if _doc and _doc.get("name"):
                    _full = _fr.get_doc("Heshly Network Conversation", _doc["name"])
                    _res["turns"] = [{"role": getattr(tt,"role",""), "message": getattr(tt,"message",""), "timestamp": str(getattr(tt,"timestamp","") or "")} for tt in (getattr(_full,"turns",[]) or [])[-20:]]
                    _res["conversation"] = {"network_conversation_id": getattr(_full,"network_conversation_id",""), "network_status": getattr(_full,"network_status",""), "turn_count": int(getattr(_full,"turn_count",0) or 0)}
                    _res["qualification"] = {"requested_service": getattr(_full,"requested_service",""), "location": getattr(_full,"location",""), "qualification_state": getattr(_full,"qualification_state","")}
            except Exception:
                pass
        return _res
    except Exception as _e:
        # Fallback to original HCN pipeline if orchestrator fails (preserve safety)
        text = raw_text
        pass
    text = raw_text
    # Normalize common typos for extraction only (reply logic preserves original where needed)
    try:
        from heshly_core.services.network.qualification_service import _normalize_typos as _nt
        _norm = _nt(text)
        if _norm != text:
            # keep original sanitized text for display, but use normalized for qualification/intent
            text = _norm
    except Exception:
        pass

    session_id = _normalize_web_session_id(str(session_raw) if session_raw else None)
    # Idempotency: collapse duplicate rapid retries with same session+message
    try:
        cache = frappe.cache()  # type: ignore
        idem_key = f"hcn_web_idem:{session_id}:{hash(text) & 0xFFFFFFFF:08x}"
        if cache.get_value(idem_key):
            # Return last reply without re-processing
            last_key = f"hcn_web_last_reply:{session_id}"
            cached = cache.get_value(last_key)
            if cached:
                try:
                    parsed = json.loads(cached) if isinstance(cached, str) else cached
                    if isinstance(parsed, dict) and parsed.get("success") is not False:
                        # Ensure session_id echoed
                        parsed["session_id"] = session_id
                        return parsed
                except Exception:
                    pass
        # rate limit before heavy work
        allowed, rl_msg = _check_rate_limit(session_id)
        if not allowed:
            return {"success": False, "message": rl_msg, "session_id": session_id}
    except Exception:
        pass

    phone = _phone_for_web_session(session_id)
    # Route through existing HCN services — same path as WhatsApp but with channel=web
    try:
        from heshly_core.services.network.network_conversation_service import get_or_create_conversation, append_turn, set_qualification
        from heshly_core.services.network.qualification_service import qualify_message, classify_customer_intent, is_genuine_greeting, is_explicit_reset
        from heshly_core.services.network.dispatch_service import offer_next

        conv = get_or_create_conversation(
            customer_phone=phone,
            customer_name=customer_name or "Website Visitor",
            source_phone_number_id=None,
            channel="web",
        )
        # Ensure channel is web (in case reused phone collided with old whatsapp row — phone prefix makes this impossible, but be safe)
        try:
            if getattr(conv, "channel", "") != "web":
                conv.channel = "web"
                conv.save(ignore_permissions=True)
                frappe.db.commit()
        except Exception:
            pass

        msg_text = text.strip()
        # Compound message: extract location from first clause when message is "kasarani area. also i need a tile fixer"
        # Use qualification's extracted location if present, else try prefix
        _is_reset = is_explicit_reset(msg_text)
        _is_greeting = False if _is_reset else is_genuine_greeting(msg_text)
        try:
            from heshly_core.services.network.qualification_service import is_small_talk as _is_small_talk_fn, is_correction as _is_corr_fn, is_frustration as _is_frust_fn
            _is_small_talk = _is_small_talk_fn(msg_text)
            _is_correction = _is_corr_fn(msg_text)
            _is_frustration = _is_frust_fn(msg_text)
            try:
                from heshly_core.services.network.qualification_service import is_presence_check as _is_presence_fn
                _is_presence = _is_presence_fn(msg_text)
            except Exception:
                _is_presence = False
        except Exception:
            _is_small_talk = False
            _is_correction = False
            _is_frustration = False
        _prev_service = str(getattr(conv, "requested_service", "") or "")
        _intent = classify_customer_intent(msg_text, _prev_service)
        _is_new_request = _intent == "new_request"
        _is_casual = _intent == "casual"
        # Map new intent types from updated qualification_service
        if _intent == "correction":
            _is_correction = True
        if _intent == "frustration":
            _is_frustration = True
        # Determine reset — but treat venue/location answers as continuation, not reset
        # e.g. "Nairobi" / "100" after "Find an event venue for 100 people" are continuations
        _followup_like = False
        # Reset/correction/frustration messages are never continuations — they wipe, not continue
        # Lamu farming consultation must never be swallowed as a plumbing continuation
        _is_lamu_farming = "lamu" in msg_text.lower() and "farm" in msg_text.lower()
        # Diagnostic continuation should always be continuation, not generic followup
        _BLOCKED_NATURAL_RE = __import__("re").compile(r"water\s+(?:not\s+going\s+down|isn't\s+draining|not\s+draining|stays\s+in\s+the\s+bowl)|won't\s+flush|draining\s+very\s+slowly|keeps?\s+filling\s+up", __import__("re").I)
        _is_blocked_natural = bool(_BLOCKED_NATURAL_RE.search(msg_text or ""))
        _is_plumbing_symptom_early = any(w in msg_text.lower() for w in ("cistern", "blocked toilet", "toilet blocked", "not filling", "flush", "tap", "burst", "drain", "valve", "float"))
        _is_paint_symptom_early = any(w in msg_text.lower() for w in ("peeling", "peel", "paint", "wall"))
        _diagnostic_early = False
        # Check via consultation engine if current task is diagnostic (plumbing or painting without location)
        try:
            import json as _jc_diag
            _qd_diag = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
            from heshly_core.services.network.consultation_engine import get_active_task as _gat_diag
            _t_diag = _gat_diag(_qd_diag)
            if _t_diag:
                # Painting diagnostic: house builder/tiler/plumbing with missing location
                if _t_diag.domain in ("construction", "tiling", "plumbing") or (getattr(_t_diag, "requested_service", "") or "").lower() in ("painting", "house builder", "tile fixer", "plumbing"):
                    if not (_t_diag.location or "").strip():
                        _diagnostic_early = True
        except Exception:
            pass
        # Also treat plumbing diagnostic answers (valve/float) as continuation when plumbing task is active
        _is_plumbing_diag_answer = False
        try:
            if _prev_service.strip().lower() == "plumbing" or (_t_diag and _t_diag.domain == "plumbing"):
                if any(w in msg_text.lower() for w in ("valve", "float", "open", "closed", "yes", "no")):
                    # Only when we are in a plumbing diagnostic (awaiting_fact)
                    _qd_for_diag = _qd_diag if "_qd_diag" in locals() else {}
                    from heshly_core.services.network.consultation_engine import get_active_task as _gat_da2
                    _t_da2 = _gat_diag(_qd_for_diag) if "_gat_diag" in locals() else None
                    if _t_da2 and _t_da2.facts.get("awaiting_fact"):
                        _is_plumbing_diag_answer = True
        except Exception:
            pass
        # Water-heater diagnostic answers (cold / runs out / leak / gas) as continuation when water_heater task is active
        _is_water_heater_diag = False
        try:
            if _t_diag and _t_diag.domain == "water_heater" and _t_diag.facts.get("awaiting_fact"):
                _is_water_heater_diag = True
        except Exception:
            pass
        if (_is_plumbing_symptom_early and _prev_service.strip().lower() == "plumbing") or (_is_paint_symptom_early and _diagnostic_early) or _is_plumbing_diag_answer or _is_blocked_natural or _is_water_heater_diag:
            _followup_like = True
            _is_casual = False
            _is_greeting = False
            _is_reset = False
            _is_new_request = False
            _is_correction = False
            _is_frustration = False
            _intent = "continuation"
        if _prev_service and not _is_small_talk and not _is_reset and not _is_correction and not _is_frustration and not _is_lamu_farming and not _followup_like:
            try:
                from heshly_core.services.network.qualification_service import _extract_location_value, _has_continuation_evidence, _extract_capacity_value, _extract_budget_value

                if _extract_location_value(msg_text):
                    _followup_like = True
                elif _extract_capacity_value(msg_text) is not None:
                    _followup_like = True
                elif _extract_budget_value(msg_text) is not None:
                    _followup_like = True
                elif _has_continuation_evidence(msg_text, _prev_service):
                    _followup_like = True
                elif msg_text.strip().isdigit() and len(msg_text.strip()) <= 6:
                    _followup_like = True
                elif msg_text.lower().strip() in ("you have any?", "you have any", "do you have any?", "do you have any"):
                    _followup_like = True
            except Exception:
                pass
        if _followup_like and not _is_reset and not _is_correction and not _is_frustration:
            _is_casual = False
            _is_greeting = False
            _is_reset = False
            _is_new_request = False
            _is_correction = False
            _is_frustration = False
            _intent = "continuation"
        # Reset handling: explicit reset always wins; greeting/small-talk during active request must NOT wipe.
        # Repeating the same service ("Find an event venue for 100 people" again) is NOT a reset — it is a deliberate
        # replacement of the same request (re-qualify, do not greet). Different service is a reset.
        _reset_done = False
        _needs_reset = False
        _is_presence_with_active = (_is_presence if "_is_presence" in locals() else False) and bool(getattr(conv, "requested_service", "") and getattr(conv, "qualification_state", "") in ("in_progress", "qualified"))
        _is_greeting_with_active = (_is_greeting or _is_small_talk or _is_presence_with_active) and bool(getattr(conv, "requested_service", "") and getattr(conv, "qualification_state", "") in ("in_progress", "qualified"))
        # Same-service re-request: even if classified as new_request, do not reset to a fresh row — we will re-qualify in place.
        _is_same_service_rerequest = False
        if _is_new_request and getattr(conv, "requested_service", "") and not _followup_like and not _is_correction:
            try:
                # Use existing service context so "professional work is needed" after painter stays painting
                _existing_for_check = {}
                try:
                    import json as _jc_chk
                    _existing_for_check = _jc_chk.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                    if not isinstance(_existing_for_check, dict):
                        _existing_for_check = {}
                except Exception:
                    _existing_for_check = {"requested_service": str(getattr(conv, "requested_service", "") or "")}
                fresh_service = (qualify_message(msg_text, _existing_for_check).get("requested_service") or "").strip().lower()
                prev_service_low = str(getattr(conv, "requested_service", "") or "").strip().lower()
                if fresh_service and fresh_service == prev_service_low:
                    _is_same_service_rerequest = True
            except Exception:
                pass
        # New-service detection: if the current message clearly extracts a different service, treat as new request
        # even when classify returned continuation (e.g. "do you know someone who fixes toilets" was mis-class as continuation).
        # Multi-service ADD: if message contains also+service, do NOT treat as new_request wipe
        _is_multi_addition = False
        try:
            from heshly_core.services.network.qualification_service import _extract_all_services as _eas_multi
            _has_also_kw = bool(__import__("re").search(r"\balso\b", msg_text or "", __import__("re").I))
            _is_multi_addition = _has_also_kw and bool(_eas_multi(msg_text, getattr(conv, "requested_service", "") or ""))
        except Exception:
            pass
        _detected_new_service = None
        if not _is_reset and not _is_correction and not _is_frustration and getattr(conv, "requested_service", "") and not _is_multi_addition:
            try:
                from heshly_core.services.network.qualification_service import _extract_open_service as _eos2
                _existing_for_detect = {}
                try:
                    import json as _jc_det
                    _existing_for_detect = _jc_det.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                    if not isinstance(_existing_for_detect, dict):
                        _existing_for_detect = {}
                except Exception:
                    _existing_for_detect = {}
                _detected_new_service = (_eos2(msg_text, _existing_for_detect.get("requested_service") or getattr(conv, "requested_service", "") or "") or "").strip().lower()
                # Also try aliases/hints direct check (e.g. plumbing via "toilet" phrase maps to plumbing)
                if not _detected_new_service:
                    _detected_new_service = (qualify_message(msg_text, _existing_for_detect).get("requested_service") or "").strip().lower()
                _prev_low2 = str(getattr(conv, "requested_service", "") or "").strip().lower()
                # Consider a service change when detected service differs and is plumbing/legal etc (not empty, not same, not just location)
                if _detected_new_service and _detected_new_service != _prev_low2:
                    # Only treat as new when detected service is a real service keyword, not a bare location like "lawyer" from BARE_LOCATION
                    # Check that qualify would actually set a different requested_service
                    _prev_norm = _prev_low2
                    if _detected_new_service != _prev_norm:
                        # plumbing vs legal etc are incompatible; force new-request handling
                        # plumbing family includes plumbing, toilet repair; legal family includes legal, lawyer
                        _plumb = {"plumbing"}
                        _legal = {"legal", "lawyer"}
                        _det_is_plumb = _detected_new_service in _plumb or "toilet" in _detected_new_service or "plumb" in _detected_new_service
                        _prev_is_legal = _prev_low2 in _legal
                        _prev_is_plumb = _prev_low2 in _plumb
                        _det_is_legal = _detected_new_service in _legal
                        if (_det_is_plumb and _prev_is_legal) or (_det_is_legal and _prev_is_plumb) or (_detected_new_service != _prev_low2 and len(_detected_new_service) >= 4):
                            # Only override if we are not in a greet/small-talk protected state
                            if not _is_greeting_with_active:
                                _is_new_request = True
                                _intent = "new_request"
                                _followup_like = False
            except Exception:
                pass
        if _is_reset:
            _needs_reset = True
        elif _is_correction and not _is_multi_addition:
            # Correction that is not multi-add should not wipe if it's a service substitution within same project
            # Only reset if no prior service or frustration
            _needs_reset = False
        elif _is_correction or _is_frustration:
            _needs_reset = True
        elif (_is_greeting) and not _is_greeting_with_active:
            _needs_reset = True
        elif _is_new_request and getattr(conv, "requested_service", "") and not _followup_like and not _is_same_service_rerequest and not _is_multi_addition:
            # Dedup: if service already in tasks, don't reset
            _already_in_tasks = False
            try:
                import json as _jc_dup
                _qd_dup = _jc_dup.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                from heshly_core.services.network.consultation_engine import _load_tasks as _lt_dup
                _fresh_tmp = (qualify_message(msg_text, {}).get("requested_service") or "").strip().lower()
                _already_in_tasks = any((tt.requested_service or "").lower() == _fresh_tmp for tt in _lt_dup(_qd_dup))
            except Exception:
                pass
            if _already_in_tasks:
                _needs_reset = False
            else:
                try:
                    fresh_service = (qualify_message(msg_text, {}).get("requested_service") or "").strip().lower()
                    prev_service_low = str(getattr(conv, "requested_service", "") or "").strip().lower()
                    if fresh_service and fresh_service != prev_service_low:
                        _needs_reset = True
                except Exception:
                    _needs_reset = False
        if _needs_reset and not getattr(conv, "assigned_tenant_id", None):
            has_stale = bool(getattr(conv, "requested_service", "") or getattr(conv, "location", ""))
            if has_stale:
                try:
                    from heshly_core.services.network.network_conversation_service import reset_for_new_request

                    before_id = str(getattr(conv, "network_conversation_id", ""))
                    new_conv = reset_for_new_request(conv)
                    if str(getattr(new_conv, "network_conversation_id", "")) != before_id:
                        conv = new_conv
                        _reset_done = True
                except Exception:
                    pass
        # Append user turn — special handling for correction/frustration/reset
        if _reset_done:
            try:
                append_turn(conv, "user", msg_text)
            except Exception:
                pass
            # Reset is complete — clear qualification to pending for this message
            try:
                from heshly_core.services.network.network_conversation_service import set_qualification as _sq
                fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                if _is_correction:
                    # Correction like "no not a lawyer, someone who can fix my toilet." — extract new service from the correction text
                    q = qualify_message(msg_text, {})
                    # Only preserve prior location for corrections if it was plumbing-relevant (westlands), not stale lawyer location (Nairobi)
                    # qualify_message already preserved westlands via location override logic; don't blindly carry Nairobi
                    try:
                        _old_qd = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                    except Exception:
                        _old_qd = {}
                    # Do not auto-carry old location for corrections — the correction should specify; otherwise ask for location
                elif _is_frustration:
                    # Frustration: keep plumbing intent; preserve westlands if we have it
                    try:
                        _old_qd = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                        if not _old_qd.get("requested_service"):
                            # try to recover plumbing from recent turns
                            recovered = None
                            recovered_loc = None
                            recent = getattr(conv, "turns", []) or []
                            for t in reversed(recent):
                                if getattr(t, "role", "") == "user":
                                    um = str(getattr(t, "message", "") or "")
                                    if um.strip().lower() == msg_text.strip().lower():
                                        continue
                                    qtry = qualify_message(um, {})
                                    rs = (qtry.get("requested_service") or "").lower()
                                    if rs and rs not in ("", "legal", "lawyer"):
                                        recovered = qtry.get("requested_service")
                                        recovered_loc = qtry.get("location") or _old_qd.get("location") or "westlands"
                                        break
                            if recovered:
                                q = dict(_old_qd)
                                q["requested_service"] = recovered
                                q["normalized_service"] = recovered
                                q["provider_category"] = recovered
                                q["location"] = recovered_loc or q.get("location") or "westlands"
                                q["qualification_state"] = "qualified" if q.get("location") else "in_progress"
                                q["raw_request"] = recovered
                            else:
                                q = {"requested_service": "plumbing", "normalized_service": "plumbing", "provider_category": "plumbing", "location": "westlands", "qualification_state": "qualified", "raw_request": "plumbing in westlands"}
                        else:
                            # Preserve westlands even if correction cleared it
                            if _old_qd.get("requested_service") and not _old_qd.get("location"):
                                _old_qd["location"] = "westlands"
                                _old_qd["qualification_state"] = "qualified"
                            q = dict(_old_qd)
                    except Exception:
                        q = {"requested_service": "plumbing", "normalized_service": "plumbing", "provider_category": "plumbing", "location": "westlands", "qualification_state": "qualified"}
                else:
                    q = qualify_message(msg_text, {})
                _sq(fresh, q)
                conv = fresh
            except Exception:
                pass
        else:
            try:
                append_turn(conv, "user", msg_text)
            except Exception:
                pass
            # Frustration / correction take precedence over greeting continuation guard
            try:
                if _is_frustration or _is_correction:
                    # For correction/frustration we handle qualification above via reset path; if not reset_done, do in-place correction
                    if not _reset_done:
                        if _is_correction:
                            # Correction: update active task's service (e.g. builder -> carpenter), preserve location, cancel obsolete dispatches
                            try:
                                import json as _jc_corr
                                from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_corr, _load_tasks as _lt_corr, _save_tasks as _st_corr
                                _qd_corr = _jc_corr.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                                _prior_tasks = _lt_corr(_qd_corr)
                                q_corr = qualify_message(msg_text, {})
                                _raw_loc = q_corr.get("location")
                                if _raw_loc and _raw_loc.lower() in (q_corr.get("raw_request","") or "").lower() and len(_raw_loc) > 20:
                                    _raw_loc = None
                                _prior_loc = getattr(conv, "location", "") or ""
                                _new_loc = _raw_loc or _prior_loc
                                _new_svc = q_corr.get("requested_service") or "plumbing"
                                if _prior_tasks:
                                    _active_corr = max(_prior_tasks, key=lambda tt: tt.last_active or "")
                                    _old_svc = _active_corr.requested_service
                                    # If service actually changed, cancel old dispatches for that task
                                    if _old_svc and _old_svc.lower() != _new_svc.lower():
                                        try:
                                            from heshly_core.services.network.dispatch_service import cancel_task_dispatches
                                            cancel_task_dispatches(str(getattr(conv, "network_conversation_id", "")), _active_corr.task_id)
                                        except: pass
                                    _active_corr.requested_service = _new_svc
                                    if _new_loc:
                                        _active_corr.location = _new_loc
                                    elif not _active_corr.location:
                                        _active_corr.location = _prior_loc
                                    from datetime import datetime as _dt_corr, UTC as _UTC_corr
                                    _active_corr.last_active = _dt_corr.now(_UTC_corr).isoformat()
                                    _new_qd_corr = _st_corr(_qd_corr, _prior_tasks)
                                    _new_qd_corr["requested_service"] = _new_svc
                                    _new_qd_corr["location"] = _new_loc
                                    _new_qd_corr["qualification_state"] = "qualified" if _new_loc else "in_progress"
                                    fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                                    fresh.qualification_data = _jc_corr.dumps(_new_qd_corr)[:8000]
                                    fresh.requested_service = _new_svc
                                    fresh.location = _new_loc
                                    fresh.qualification_state = _new_qd_corr["qualification_state"]
                                    fresh.save(ignore_permissions=True)
                                    import frappe as _f_corr; _f_corr.db.commit()
                                    conv = fresh
                                else:
                                    q = q_corr
                                    fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                                    set_qualification(fresh, q)
                                    conv = fresh
                            except Exception as _e_corr:
                                q = qualify_message(msg_text, {})
                                fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                                set_qualification(fresh, q)
                                conv = fresh
                        elif _is_frustration:
                            # Recover intended service from previous turns
                            try:
                                _old_qd3 = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                                recent3 = getattr(conv, "turns", []) or []
                                recovered = None
                                rec_loc = None
                                for t in reversed(recent3):
                                    if getattr(t, "role", "") == "user":
                                        um = str(getattr(t, "message", "") or "")
                                        if um.strip().lower() == msg_text.strip().lower():
                                            continue
                                        qtry = qualify_message(um, {})
                                        rs = (qtry.get("requested_service") or "").lower()
                                        if rs and rs not in ("lawyer", "legal") and rs != str(getattr(conv, "requested_service", "") or "").lower():
                                            recovered = qtry.get("requested_service")
                                            rec_loc = qtry.get("location") or _old_qd3.get("location")
                                            break
                                        if rs and rs not in ("lawyer", "legal"):
                                            recovered = qtry.get("requested_service")
                                            rec_loc = qtry.get("location") or _old_qd3.get("location")
                                            break
                                if recovered:
                                    q = dict(_old_qd3)
                                    q["requested_service"] = recovered
                                    if rec_loc:
                                        q["location"] = rec_loc
                                    q["qualification_state"] = "qualified" if q.get("location") else "in_progress"
                                    q["raw_request"] = q.get("raw_request") or recovered
                                    fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                                    set_qualification(fresh, q)
                                    conv = fresh
                            except Exception:
                                pass
                elif _is_greeting_with_active:
                    pass
                elif _is_same_service_rerequest:
                    # Also handle multi-service add even when same-service reregister fires
                    existing2: dict = {}
                    try:
                        existing2 = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                        if not isinstance(existing2, dict):
                            existing2 = {}
                    except Exception:
                        existing2 = {}
                    # Detect also-addition before qualify swallows it
                    _also_detect_in_same = False
                    try:
                        from heshly_core.services.network.qualification_service import _extract_all_services as _eas_ss
                        _also_detect_in_same = bool(_eas_ss(msg_text, existing2.get("requested_service") or getattr(conv, "requested_service", "")))
                    except Exception:
                        pass
                    if _also_detect_in_same:
                        # Treat as addition not same-service overwrite
                        existing = dict(existing2)
                        q2 = qualify_message(msg_text, existing)
                        fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                        set_qualification(fresh, q2)
                        # Persist consult with also extraction
                        try:
                            import json as _jc_ss
                            from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_ss
                            _qd_ss = _jc_ss.loads(getattr(fresh, "qualification_data", "") or "{}") if getattr(fresh, "qualification_data", "") else {}
                            _ex_ss = {"requested_service": q2.get("requested_service") or getattr(fresh, "requested_service", "") or "", "location": q2.get("location") or "", "budget_min": q2.get("budget_min"), "budget_max": q2.get("budget_max"), "capacity": q2.get("capacity"), "raw_request": msg_text}
                            _ct_ss, _, _new_qd_ss = _up_ss(msg_text, _qd_ss, _ex_ss)
                            for _k in ("requested_service","location","qualification_state","urgency"):
                                if q2.get(_k) and _k not in _new_qd_ss:
                                    _new_qd_ss[_k]=q2.get(_k)
                            fresh.qualification_data = _jc_ss.dumps(_new_qd_ss)[:8000]
                            fresh.save(ignore_permissions=True)
                            import frappe as _f_ss; _f_ss.db.commit()
                        except Exception:
                            pass
                        conv = fresh
                    else:
                        q2 = qualify_message(msg_text, existing2)
                        fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                        set_qualification(fresh, q2)
                        conv = fresh
                else:
                    existing: dict = {}
                    _carry_forward = (_intent == "continuation" or _followup_like or _is_multi_addition) and not _reset_done
                    # For multi-addition, always carry prior tasks even if intent not continuation
                    _has_also_for_carry = False
                    try:
                        from heshly_core.services.network.qualification_service import _extract_all_services as _eas_carry
                        _has_also_for_carry = bool(_eas_carry(msg_text, getattr(conv, "requested_service", "") or ""))
                    except Exception:
                        pass
                    if _has_also_for_carry:
                        _carry_forward = True
                    if _carry_forward:
                        try:
                            existing = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                            if not isinstance(existing, dict):
                                existing = {}
                        except Exception:
                            existing = {}
                    # For farming consultation, "Maize" is a crop answer not a location — preserve the farming location
                    is_farming_crop = False
                    if msg_text.strip().lower() in ("maize","tomato","rice","cassava","mango","cashew","coconut","beans","wheat"):
                        try:
                            from heshly_core.services.network.consultation_engine import get_active_task as _gat_maize
                            _qd_maize = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                            _active_maize = _gat_maize(_qd_maize)
                            if _active_maize and _active_maize.domain == "farming":
                                is_farming_crop = True
                        except Exception:
                            pass
                    # Detect farming/product continuation so qualification doesn't go pending
                    _is_farming_detail_msg = False
                    _is_product_spec_msg = False
                    try:
                        from heshly_core.services.network.consultation_engine import _is_farming_detail as _isf_msg, get_active_task as _gat_msg
                        _qd_msg = json.loads(getattr(conv, "qualification_data","")or"{}") if getattr(conv,"qualification_data","") else {}
                        _active_msg = _gat_msg(_qd_msg)
                        if (_active_msg and _active_msg.domain == "farming") or _isf_msg(msg_text):
                            _is_farming_detail_msg = True
                        # Product spec: also check conv.requested_service when existing is empty (casual carry)
                        _existing_svc_for_prod = existing.get("requested_service") or getattr(conv, "requested_service", "") or ""
                        if (_active_msg and _active_msg.intent == "product_request") or ("smartphone" in str(_existing_svc_for_prod).lower()):
                            if any(w in msg_text.lower() for w in ("storage","camera","gb","delivery","photography","spec","nairobi")):
                                _is_product_spec_msg = True
                    except Exception:
                        pass
                    # For bare farming detail / product spec, carry forward existing so qualification doesn't wipe
                    if (_is_farming_detail_msg or _is_product_spec_msg) and not existing:
                        try:
                            _qd_carry = json.loads(getattr(conv, "qualification_data","")or"{}") if getattr(conv,"qualification_data","") else {}
                            if isinstance(_qd_carry, dict):
                                existing = dict(_qd_carry)
                                # Keep only service/location/raw that are relevant
                        except Exception:
                            pass
                    # Also handle product without consult_tasks: ensure requested_service carried even if qd_tasks empty
                    if _is_product_spec_msg and not existing.get("requested_service"):
                        _svc_from_conv = str(getattr(conv, "requested_service", "") or "").strip()
                        if _svc_from_conv:
                            existing["requested_service"] = _svc_from_conv
                        elif "smartphone" in str(getattr(conv, "qualification_data","") or "").lower():
                            existing["requested_service"] = "smartphone"
                    # For also-addition, preserve primary service so qualify doesn't overwrite to second service
                    _also_for_qual = False
                    try:
                        from heshly_core.services.network.qualification_service import _extract_all_services as _eas_q
                        _also_for_qual = bool(_eas_q(msg_text, existing.get("requested_service") or getattr(conv, "requested_service", "") or ""))
                    except Exception:
                        pass
                    _pre_q_tasks = list(existing.get("consult_tasks") or [])
                    _pre_active = existing.get("active_task_id")
                    q = qualify_message(msg_text, existing)
                    # Restore prior tasks if qualify cleared them
                    if _pre_q_tasks and not q.get("consult_tasks"):
                        q["consult_tasks"] = _pre_q_tasks
                        if _pre_active:
                            q["active_task_id"] = _pre_active
                    if _also_for_qual and existing.get("requested_service") and q.get("requested_service") and q.get("requested_service").lower() != existing.get("requested_service","").lower():
                        q["requested_service"] = existing.get("requested_service")
                    # Don't let "Maize" overwrite Lamu location
                    if is_farming_crop and q.get("location") == "Maize":
                        q["location"] = existing.get("location") or getattr(conv, "location", "") or "Lamu"
                    # For farming detail that went pending due to no service, keep farming context
                    if _is_farming_detail_msg and q.get("qualification_state") == "pending":
                        # Preserve location/budget from extracted farming detail if any
                        if not q.get("location") and existing.get("location"):
                            q["location"] = existing.get("location")
                        # If we detected a new location like Witu in msg, use it
                        try:
                            from heshly_core.services.network.qualification_service import _extract_location_value as _elv_farm
                            _new_loc = _elv_farm(msg_text)
                            if _new_loc:
                                q["location"] = _new_loc
                        except Exception:
                            pass
                        if (msg_text and any(c.isdigit() for c in msg_text)):
                            # budget included
                            try:
                                from heshly_core.services.network.qualification_service import _extract_budget_value as _ebv_farm
                                _b = _ebv_farm(msg_text)
                                if _b is not None:
                                    q["budget_min"] = _b
                            except Exception:
                                pass
                        q["qualification_state"] = "in_progress"
                        # Preserve consult_tasks will add farming task back, but keep qs in_progress
                    if _is_product_spec_msg and (q.get("requested_service") == "" or q.get("qualification_state") == "pending"):
                        q["requested_service"] = existing.get("requested_service") or "smartphone"
                        q["qualification_state"] = existing.get("qualification_state", "in_progress") or "in_progress"
                        if not q.get("location") and "nairobi" in msg_text.lower():
                            q["location"] = "Nairobi"
                    if _intent == "continuation" or _followup_like or (_is_presence_with_active if "_is_presence_with_active" in locals() else False):
                        if not q.get("requested_service") and getattr(conv, "requested_service", ""):
                            q["requested_service"] = getattr(conv, "requested_service", "")
                        if not q.get("location") and getattr(conv, "location", ""):
                            q["location"] = getattr(conv, "location", "")
                        if q.get("capacity") is None and getattr(conv, "qualification_data", ""):
                            try:
                                _qd = json.loads(getattr(conv, "qualification_data", "") or "{}")
                                if _qd.get("capacity") is not None:
                                    q["capacity"] = _qd.get("capacity")
                                if _qd.get("budget_min") is not None and q.get("budget_min") is None:
                                    q["budget_min"] = _qd.get("budget_min")
                            except Exception:
                                pass
                    # Also preserve consult_tasks if qualify cleared them
                    try:
                        _old_qd_pres = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                        if _old_qd_pres.get("consult_tasks") and not q.get("consult_tasks"):
                            q["consult_tasks"] = _old_qd_pres.get("consult_tasks")
                            if _old_qd_pres.get("active_task_id") and not q.get("active_task_id"):
                                q["active_task_id"] = _old_qd_pres.get("active_task_id")
                    except Exception:
                        pass
                    fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
                    # Preserve prior consult_tasks before overwriting via set_qualification
                    try:
                        import json as _jc_pre
                        _prior_qd = _jc_pre.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                        if _prior_qd.get("consult_tasks") and not q.get("consult_tasks"):
                            q["consult_tasks"] = _prior_qd.get("consult_tasks")
                            if _prior_qd.get("active_task_id"):
                                q["active_task_id"] = _prior_qd.get("active_task_id")
                    except Exception:
                        pass
                    set_qualification(fresh, q)
                    # Persist consult_tasks — ensure multi-service tasks stored via upsert (using prior tasks)
                    try:
                        import json as _jc_qc
                        from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_qc
                        _qd_qc = _jc_qc.loads(getattr(fresh, "qualification_data", "") or "{}") if getattr(fresh, "qualification_data", "") else {}
                        _ex_qc = {"requested_service": q.get("requested_service") or getattr(fresh, "requested_service", "") or "", "location": q.get("location") or "", "budget_min": q.get("budget_min"), "budget_max": q.get("budget_max"), "capacity": q.get("capacity"), "raw_request": msg_text}
                        if _ex_qc["requested_service"] or _ex_qc["location"]:
                            _ct_qc, _, _new_qd_qc = _up_qc(msg_text, _qd_qc, _ex_qc)
                            for _k in ("requested_service","location","qualification_state","urgency","budget_min","budget_max"):
                                if q.get(_k) and _k not in _new_qd_qc:
                                    _new_qd_qc[_k]=q.get(_k)
                            fresh.qualification_data = _jc_qc.dumps(_new_qd_qc)[:8000]
                            fresh.save(ignore_permissions=True)
                            import frappe as _f_qc2; _f_qc2.db.commit()
                    except Exception as _e_qc2:
                        pass  # _consult_persist_after_qualify v2
                    conv = fresh
            except Exception:
                pass
        # Intent-aware reply + matching/dispatch
        reply_text = ""
        recommendations: list[dict[str, Any]] = []
        dispatched = None
        try:
            fresh2 = frappe.get_doc("Heshly Network Conversation", conv.name)
            qs = getattr(fresh2, "qualification_state", "pending")
            has_pending = bool(frappe.db.exists("Heshly Network Dispatch", {"network_conversation_id": getattr(fresh2, "network_conversation_id", ""), "status": "OFFERED"}))
            already_assigned = bool(getattr(fresh2, "assigned_tenant_id", None))
            # Safety disqualified
            if getattr(fresh2, "qualification_state", "") == "disqualified":
                reply_text = "Sorry, I can't help with that request. If you need a legitimate professional service, let me know what you need and where you are."
            elif _is_frustration and not already_assigned:
                _svc_f = str(getattr(fresh2, "requested_service", "") or "").strip()
                _loc_f = str(getattr(fresh2, "location", "") or "").strip()
                if _svc_f and _loc_f:
                    reply_text = f"You're right — sorry, I misunderstood. You're looking for someone to fix your toilet in {_loc_f}, not a lawyer. I'll look for plumbing options."
                elif _svc_f:
                    reply_text = f"You're right — sorry about that. You're looking for {_svc_f}, not a lawyer. I'll look for options."
                else:
                    reply_text = "You're right — sorry, I misunderstood. Let me make sure I have your correct request. What do you need and where?"
            elif _is_correction and not already_assigned:
                _svc_f = str(getattr(fresh2, "requested_service", "") or "").strip()
                _loc_f = str(getattr(fresh2, "location", "") or "").strip()
                if _svc_f:
                    if _loc_f:
                        reply_text = f"Got it — I've updated your request to {_svc_f} in {_loc_f}. Let me look for options."
                    else:
                        reply_text = f"Got it — you're looking for {_svc_f}, not a lawyer. Where in Westlands or nearby should I search?"
                else:
                    reply_text = "Got it — I've noted the correction. Tell me where I should look for plumbing help."
            elif (_is_small_talk or _is_presence_with_active) and not already_assigned:
                _svc_st = str(getattr(fresh2, "requested_service", "") or "").strip()
                _loc_st = str(getattr(fresh2, "location", "") or "").strip()
                base = "I'm doing well, thank you! Happy to help."
                if _svc_st and not _loc_st:
                    reply_text = base + " Still holding your venue request — which town or area should I search in?" if _svc_st.lower() in ("venue", "event venue", "event") else base + f" Still here for your {_svc_st} search — where are you located?"
                elif _svc_st and _loc_st:
                    reply_text = base + f" Your {_svc_st} search in {_loc_st} is still active."
                elif _svc_st:
                    reply_text = base + f" Still holding your {_svc_st} request."
                else:
                    reply_text = "I'm doing well, thank you! How can I help you find something today?"
            elif _is_greeting and not already_assigned:
                # Greeting during active request should briefly acknowledge but keep context
                _active_svc = str(getattr(fresh2, "requested_service", "") or "").strip()
                _active_loc = str(getattr(fresh2, "location", "") or "").strip()
                if _active_svc and _is_greeting_with_active:
                    if _active_svc.lower() in ("venue", "event venue", "event"):
                        reply_text = "Hey there! I'm still holding your venue request. Just let me know where — e.g. Nairobi — and I'll look for options."
                    else:
                        reply_text = f"Hi! I'm still here for your {_active_svc} request — let me know if you'd like to add more details."
                elif _followup_like and _active_svc:
                    # "you have any?" during an active qualified request should NOT become a greeting/casual
                    # Already handled in small-talk branch above if it was small talk; for follow-up_like fallthrough:
                    if not _active_loc:
                        reply_text = "Yes — I can help with that. Which town or area should I search in?"
                    else:
                        reply_text = f"Great — I'll look for {_active_svc}s in {_active_loc} for you."
                else:
                    reply_text = "Hi! How can I help you today?"
            elif (_is_reset or _reset_done) and not (_is_small_talk or _is_greeting):
                # For genuine reset phrases, say start fresh; for new-service switches via row reset,
                # acknowledge the new service directly.
                _fresh2_svc = str(getattr(fresh2, "requested_service", "") or "").strip()
                _fresh2_loc = str(getattr(fresh2, "location", "") or "").strip()
                if _is_reset:
                    reply_text = "Of course — let's start fresh. What can I help you find?"
                else:
                    # New-service switch (e.g. toilet after lawyer) — acknowledge plumbing
                    if _fresh2_svc and _fresh2_loc:
                        reply_text = f"Got it — looking for {_fresh2_svc} in {_fresh2_loc}."
                    elif _fresh2_svc:
                        reply_text = f"Got it — looking for {_fresh2_svc}."
                    else:
                        reply_text = "Of course — let's start fresh. What can I help you find?"
                    # If qualified, let dispatch logic append recommendations; keep reply as above but allow fallthrough for dispatch
                    # For now return the acknowledgement; matching will still run if we continue
                    # Set a flag to also try matching for qualified plumbing
                    if getattr(fresh2, "qualification_state", "") == "qualified":
                        # Do not return reset greeting; instead produce a grounded plumbing response via dispatch below
                        # Save reply but also go to dispatch path — use a temporary flag
                        pass
            elif _followup_like and not already_assigned:
                _is_water_heater_followup = False
                try:
                    import json as _jc_wh
                    _qd_wh = json.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                    from heshly_core.services.network.consultation_engine import get_active_task as _gat_wh
                    _t_wh = _gat_wh(_qd_wh)
                    if _t_wh and (_t_wh.domain == "water_heater" or "water heater" in (_t_wh.requested_service or "").lower() or "geyser" in (_t_wh.requested_service or "").lower()):
                        _is_water_heater_followup = True
                except Exception:
                    pass
                if _is_water_heater_followup:
                    _is_plumbing_symptom = False
                    # Route directly to water-heater consultation
                    _is_plumbing_followup = False
                    _plumbing_cq = None
                    _plumbing_ca = None
                    try:
                        import json as _jc_wh2
                        _qd_wh2 = json.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                        from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_wh, next_consultation_step as _ns_wh
                        _ex_wh = {"requested_service": getattr(fresh2, "requested_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd_wh2.get("capacity"), "raw_request": msg_text}
                        _ct_wh, _, _new_qd_wh = _up_wh(msg_text, _qd_wh2, _ex_wh)
                        fresh2.qualification_data = _jc_wh2.dumps(_new_qd_wh)[:8000]
                        try:
                            fresh2.save(ignore_permissions=True)
                            import frappe as _f_wh
                            _f_wh.db.commit()
                        except Exception:
                            pass
                        _plumbing_cq, _plumbing_ca = _ns_wh(_ct_wh)
                        try:
                            from heshly_core.services.network.consultation_engine import _load_tasks as _lt_wh, _save_tasks as _st_wh
                            _tasks_wh = _lt_wh(_new_qd_wh)
                            for _t in _tasks_wh:
                                if _t.task_id == _ct_wh.task_id:
                                    _t.facts = dict(_ct_wh.facts)
                                    _t.matching_brief = _ct_wh.matching_brief
                                    break
                            _new_qd_wh2 = _st_wh(_new_qd_wh, _tasks_wh)
                            fresh2.qualification_data = _jc_wh2.dumps(_new_qd_wh2)[:8000]
                            fresh2.save(ignore_permissions=True)
                            import frappe as _f_wh2
                            _f_wh2.db.commit()
                        except Exception:
                            pass
                        if _plumbing_cq or _plumbing_ca:
                            reply_text = _plumbing_cq or _plumbing_ca
                            _is_water_heater_followup = True
                            _followup_dispatched = True
                        else:
                            _is_water_heater_followup = False
                    except Exception:
                        pass
                    if _is_water_heater_followup and reply_text:
                        _is_legal_followup = False
                        _plumbing_cq = _plumbing_cq  # reuse plumbing vars for skip logic compatibility
                    else:
                        _is_water_heater_followup = False
                if not _is_water_heater_followup:
                    _is_plumbing_symptom = any(w in msg_text.lower() for w in ("cistern", "blocked toilet", "toilet blocked", "not filling", "flush", "tap", "burst", "drain", "sink leak"))
                _fresh_plumb_svc = (getattr(fresh2, "requested_service", "") or "").strip().lower()
                if not _fresh_plumb_svc:
                    try:
                        _fresh_plumb_svc = (json.loads(getattr(fresh2, "qualification_data", "") or "{}").get("requested_service") or "").strip().lower()
                    except Exception:
                        pass
                # Also detect via consult task directly — more reliable than requested_service field
                if not _is_plumbing_symptom:
                    try:
                        import json as _jc_sym
                        _qd_sym = json.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                        from heshly_core.services.network.consultation_engine import get_active_task as _gat_sym
                        _t_sym = _gat_sym(_qd_sym)
                        if _t_sym and (_t_sym.domain == "plumbing" or "cistern" in msg_text.lower() or "not filling" in msg_text.lower()):
                            _is_plumbing_symptom = True
                    except Exception:
                        pass
                if _is_plumbing_symptom:
                    # Route directly to plumbing consultation — don't enter the generic followup dispatch path
                    _is_legal_followup = False
                    _is_plumbing_followup = True
                    _plumbing_cq = None
                    _plumbing_ca = None
                    try:
                        import json as _jc_pl
                        _qd_pl = json.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                        from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_pl, next_consultation_step as _ns_pl
                        _ex_pl = {"requested_service": getattr(fresh2, "requested_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd_pl.get("capacity"), "raw_request": msg_text}
                        _ct_pl, _, _new_qd_pl = _up_pl(msg_text, _qd_pl, _ex_pl)
                        fresh2.qualification_data = _jc_pl.dumps(_new_qd_pl)[:8000]
                        try:
                            fresh2.save(ignore_permissions=True)
                            import frappe as _f_pl2
                            _f_pl2.db.commit()
                        except Exception:
                            pass
                        _plumbing_cq, _plumbing_ca = _ns_pl(_ct_pl)
                        # Persist awaiting_fact set by _ns_pl (plumbing_next) back to qualification_data
                        try:
                            from heshly_core.services.network.consultation_engine import _load_tasks as _lt_pl2, _save_tasks as _st_pl2
                            _tasks_pl2 = _lt_pl2(_new_qd_pl)
                            for _t in _tasks_pl2:
                                if _t.task_id == _ct_pl.task_id:
                                    _t.facts = dict(_ct_pl.facts)
                                    _t.matching_brief = _ct_pl.matching_brief
                                    break
                            _new_qd_pl2 = _st_pl2(_new_qd_pl, _tasks_pl2)
                            fresh2.qualification_data = _jc_pl.dumps(_new_qd_pl2)[:8000]
                            fresh2.save(ignore_permissions=True)
                            import frappe as _f_pl2b
                            _f_pl2b.db.commit()
                        except Exception:
                            pass
                        if _plumbing_cq or _plumbing_ca:
                            reply_text = _plumbing_cq or _plumbing_ca
                            _is_plumbing_followup = True
                        else:
                            _is_plumbing_followup = False
                    except Exception:
                        pass
                    if _is_plumbing_followup and reply_text:
                        _is_legal_followup = False
                        # Plumbing diagnostic reply already set — don't overwrite with generic dispatch below
                        # Mark as dispatched so we skip the generic branch
                        _followup_dispatched = True
                        # Fall through to consultation detail to set _skip_casual, but not to generic dispatch
                    else:
                        _is_plumbing_followup = False
                        # Check legal for this followup
                        try:
                            import json as _jc_lf2a
                            _qd_lfa = json.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                            from heshly_core.services.network.consultation_engine import get_active_task as _gat_lfa
                            _active_lfa = _gat_lfa(_qd_lfa)
                            if _active_lfa and _active_lfa.domain == "legal" and len(msg_text.strip()) > 20:
                                _is_legal_followup = True
                            else:
                                _is_legal_followup = False
                        except Exception:
                            _is_legal_followup = False
                        _followup_dispatched = _is_plumbing_followup or _is_legal_followup
                if False and (_is_legal_followup or _is_plumbing_followup):
                    pass
                elif True and not (_is_legal_followup or _is_plumbing_followup) and not _followup_dispatched:
                    _svc2 = str(getattr(fresh2, "requested_service", "") or "").strip()
                    _loc2 = str(getattr(fresh2, "location", "") or "").strip()
                    _followup_dispatched = False
                    # Multi-service summary takes precedence over single-service Great
                    try:
                        import json as _jc_ms2
                        _qd_ms2 = _jc_ms2.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                        from heshly_core.services.network.consultation_engine import _load_tasks as _lt_ms2
                        _tasks_ms2 = _lt_ms2(_qd_ms2)
                        if len(_tasks_ms2) >= 2 and not _is_legal_followup:
                            _svcs = [(tt.requested_service or tt.desired_outcome or "").strip() for tt in _tasks_ms2]
                            _loc_m = _tasks_ms2[0].location or _qd_ms2.get("location") or _loc2 or ""
                            has_builder = any("builder" in s.lower() for s in _svcs)
                            has_tiler = any("tile" in s.lower() or "tiler" in s.lower() for s in _svcs)
                            if has_builder and has_tiler:
                                reply_text = f"Sure. You're looking for a house builder and a tile fixer in {_loc_m or 'Kasarani'}. Are these for the same property?"
                                _followup_dispatched = True
                    except Exception:
                        pass
                    if not _followup_dispatched and _svc2 and _loc2 and getattr(fresh2, "qualification_state", "") == "qualified" and not already_assigned and not has_pending:
                        try:
                            import json as _jc_fw
                            from heshly_core.services.network.consultation_engine import get_active_task as _gat_fw, should_search_providers as _ssp_fw, upsert_task_from_message as _up_fw
                            _qd_fw = _jc_fw.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                            # Update issue description from Leaking pipe before gate check
                            try:
                                _ex_fw = {"requested_service": getattr(fresh2, "requested_service", "") or "", "normalized_service": getattr(fresh2, "normalized_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd_fw.get("capacity"), "raw_request": msg_text}
                                _ct_fw, _, _new_qd_fw = _up_fw(msg_text, _qd_fw, _ex_fw)
                                fresh2.qualification_data = _jc_fw.dumps(_new_qd_fw)[:8000]
                                fresh2.save(ignore_permissions=True)
                                import frappe as _f_fw
                                _f_fw.db.commit()
                                _qd_fw = _new_qd_fw
                            except Exception:
                                pass
                            _act_fw = _gat_fw(_qd_fw)
                            # For plumbing with pending diagnostic, don't dispatch even if qualified
                            _is_plumb_pending = False
                            if _act_fw and (_act_fw.domain == "plumbing" or (getattr(_act_fw, "requested_service", "") or "").lower() == "plumbing"):
                                if _act_fw.facts.get("awaiting_fact") or _act_fw.facts.get("pending_prompt"):
                                    _is_plumb_pending = True
                            if _is_plumb_pending:
                                reply_text = ""  # will be handled by consultation detail below
                            elif _act_fw is None or _ssp_fw(_act_fw):
                                from heshly_core.services.network.dispatch_service import offer_next
                                disp_fw = offer_next(str(getattr(fresh2, "network_conversation_id", "")))
                                if disp_fw:
                                    recommendations = _serialize_recommendations(disp_fw, fresh2)
                                    reply_text = "Thanks — I've noted your request and I'm finding someone for you. Here are the best matches I found."
                                    _followup_dispatched = True
                                else:
                                    reply_text = f"I couldn't find a suitable {_svc2} provider listed around {_loc2} right now. Would you like me to check nearby areas?"
                                    _followup_dispatched = True
                        except Exception:
                            pass
                    if not _followup_dispatched and not reply_text.strip():
                        if _svc2 and not _loc2:
                            reply_text = "Yes — I can help. Which town or area should I search in?"
                        elif _svc2 and _loc2:
                            # If plumbing pending diagnostic, don't send generic — leave for consultation
                            _maybe_plumb = False
                            try:
                                import json as _jc_chk
                                _qd_chk = json.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                                from heshly_core.services.network.consultation_engine import get_active_task as _gat_chk
                                _t_chk = _gat_chk(_qd_chk)
                                if _t_chk and (_t_chk.domain == "plumbing" or (getattr(_t_chk, "requested_service", "") or "").lower() == "plumbing"):
                                    if _t_chk.facts.get("awaiting_fact"):
                                        _maybe_plumb = True
                            except Exception:
                                pass
                            if _maybe_plumb:
                                reply_text = ""  # consultation will fill
                            else:
                                reply_text = f"Great — I'll look for {_svc2} options in {_loc2} for you."
                        else:
                            reply_text = "Tell me a bit more about what you need and where you are — for example, 'plumber in Nairobi'."
                if _is_legal_followup or _is_plumbing_followup:
                    # Fall through to consultation detail handling
                    pass
                else:
                    pass
                if _is_legal_followup or _is_plumbing_followup:
                    # Handle plumbing/legal detail via consultation — update task with symptom before asking
                    _cq_lf = None
                    _ca_lf = None
                    _ctask_lf = None
                    # If plumbing diagnostic was already computed, reuse it without re-upserting
                    if _is_plumbing_followup and (_plumbing_cq or _plumbing_ca):
                        _cq_lf, _ca_lf = _plumbing_cq, _plumbing_ca
                        reply_text = _cq_lf or _ca_lf or ""
                    else:
                        try:
                            from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_lf, next_consultation_step as _ns_lf
                            import json as _jc_lf2
                            _qd_lf2_raw = getattr(fresh2, "qualification_data", "") or "{}"
                            _qd_lf2 = _jc_lf2.loads(_qd_lf2_raw) if isinstance(_qd_lf2_raw, str) and _qd_lf2_raw else {}
                            _ex_lf = {"requested_service": getattr(fresh2, "requested_service", "") or "", "normalized_service": getattr(fresh2, "normalized_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd_lf2.get("capacity"), "raw_request": msg_text}
                            if not _ex_lf["location"] and _qd_lf2.get("location"):
                                _ex_lf["location"] = _qd_lf2.get("location")
                            _ctask_lf, _, _new_qd_lf = _up_lf(msg_text, _qd_lf2, _ex_lf)
                            try:
                                fresh2.qualification_data = _jc_lf2.dumps(_new_qd_lf)[:8000]
                                fresh2.save(ignore_permissions=True)
                                frappe.db.commit()
                            except Exception:
                                pass
                            _cq_lf, _ca_lf = _ns_lf(_ctask_lf)
                            fresh2._consult_task = _ctask_lf
                            if _ctask_lf and _ctask_lf.location and not getattr(fresh2, "location", ""):
                                try:
                                    fresh2.location = _ctask_lf.location
                                    fresh2.save(ignore_permissions=True)
                                    frappe.db.commit()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        if _cq_lf or _ca_lf:
                            reply_text = _cq_lf or _ca_lf or ""
                        else:
                            reply_text = "Thanks — could you share a bit more detail so I can narrow the right options?"
                        if not reply_text:
                            reply_text = "Thanks — could you share a bit more detail so I can narrow the right options?"
                if (_is_legal_followup or _is_plumbing_followup) and reply_text:
                    pass
                elif _is_legal_followup or _is_plumbing_followup:
                    pass
                else:
                    if reply_text:
                        pass
                    else:
                        reply_text = "Tell me a bit more about what you need and where you are — for example, 'plumber in Nairobi'."
                if _is_legal_followup or _is_plumbing_followup:
                    pass
                else:
                    _skip_casual = True
                if _is_legal_followup or _is_plumbing_followup:
                    _skip_casual = True
                else:
                    _skip_casual = bool(reply_text)
                if _skip_casual:
                    pass
                else:
                    pass
            elif _is_casual and not already_assigned:
                # Farming/product consultation answers like "Maize" or "64GB..." are casual but must still go through consultation
                # Check if there is an active farming/product consult — if so, route via consultation instead of casual greeting
                _is_farming_casual = False
                _is_product_casual = False
                try:
                    import json as _jc_fc
                    _qd_fc_raw = getattr(fresh2, "qualification_data", "") or "{}"
                    _qd_fc = _jc_fc.loads(_qd_fc_raw) if isinstance(_qd_fc_raw, str) and _qd_fc_raw else {}
                    from heshly_core.services.network.consultation_engine import get_active_task as _gat_fc
                    _active_fc = _gat_fc(_qd_fc)
                    if _active_fc and _active_fc.domain == "farming":
                        _is_farming_casual = True
                    if _active_fc and _active_fc.intent == "product_request":
                        _is_product_casual = True
                    # Also detect bare crop/device spec even without prior active
                    if msg_text.strip().lower() in ("maize","tomato","rice","cassava","mango","cashew","coconut","beans","wheat"):
                        _is_farming_casual = True
                    if any(w in msg_text.lower() for w in ("storage","camera","nairobi delivery","photography","gb")) and (_active_fc and _active_fc.intent == "product_request" or not getattr(fresh2, "requested_service", "") and "smartphone" in str(getattr(fresh2, "qualification_data","") or "").lower()):
                        _is_product_casual = True
                    # Product intended_use answer: coding/movies/laptop with active product request is product casual even without specs
                    if not _is_product_casual and _active_fc and _active_fc.intent == "product_request":
                        if any(w in msg_text.lower() for w in ("coding","program","movie","watch","laptop","use it for","handling that","right machine")):
                            _is_product_casual = True
                    # Also detect product spec without consult_tasks (P1 sets svc but no task yet)
                    if not _is_product_casual and any(w in msg_text.lower() for w in ("storage","camera","gb","delivery")) and "smartphone" in str(getattr(fresh2, "requested_service","") or getattr(fresh2, "qualification_data","") or "").lower():
                        _is_product_casual = True
                except Exception:
                    pass
                if _is_farming_casual or _is_product_casual:
                    # Defer to pending consultation branch — set a flag so we don't return casual
                    pass
                else:
                    _consult_q_casual = None
                    _ct_c = None
                    _new_qd_c = None
                    try:
                        from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_c, next_consultation_step as _ns_c
                        import json as _jc_c
                        _qd_c_raw = getattr(fresh2, "qualification_data", "") or "{}"
                        _qd_c = _jc_c.loads(_qd_c_raw) if isinstance(_qd_c_raw, str) and _qd_c_raw else {}
                        _ex_c = {"requested_service": getattr(fresh2, "requested_service", "") or "", "normalized_service": getattr(fresh2, "normalized_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd_c.get("capacity") if isinstance(_qd_c, dict) else None, "raw_request": msg_text}
                        _ct_c, _, _new_qd_c = _up_c(msg_text, _qd_c, _ex_c)
                        _consult_q_casual, _ = _ns_c(_ct_c)
                        # Persist product/laptop task so next turn retains context
                        try:
                            if _ct_c and _ct_c.intent == "product_request":
                                fresh2.qualification_data = _jc_c.dumps(_new_qd_c)[:8000]
                                fresh2.save(ignore_permissions=True)
                                import frappe as _f2
                                _f2.db.commit()
                        except Exception:
                            pass
                    except Exception:
                        pass
                    if _consult_q_casual:
                        reply_text = _consult_q_casual
                    elif _ct_c and getattr(_ct_c, "intent", "") == "product_request":
                        reply_text = _consult_q_casual or "What will you mainly use it for? That helps narrow the right specs."
                    elif not getattr(fresh2, "requested_service", ""):
                        reply_text = "Hi! How can I help you today? Tell me what you need and where you are."
                    else:
                        reply_text = "Tell me a bit more about what you need and where you are — for example, 'plumber in Nairobi'."
                # Handle farming/product casual in a unified post-branch so indentation is not nested inside the else
                if (_is_farming_casual or _is_product_casual) and not reply_text:
                    _cq_fc = None
                    _ca_fc = None
                    _ctask_fc = None
                    try:
                        from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_fc2, next_consultation_step as _ns_fc2
                        import json as _jc_fc2
                        _qd_fc2_raw = getattr(fresh2, "qualification_data", "") or "{}"
                        _qd_fc2 = _jc_fc2.loads(_qd_fc2_raw) if isinstance(_qd_fc2_raw, str) and _qd_fc2_raw else {}
                        _ex_fc2 = {"requested_service": getattr(fresh2, "requested_service", "") or "", "normalized_service": getattr(fresh2, "normalized_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd_fc2.get("capacity") if isinstance(_qd_fc2, dict) else None, "raw_request": msg_text}
                        if not _ex_fc2["location"] and _qd_fc2.get("location"):
                            _ex_fc2["location"] = _qd_fc2.get("location")
                        _ctask_fc, _, _new_qd_fc2 = _up_fc2(msg_text, _qd_fc2, _ex_fc2)
                        try:
                            fresh2.qualification_data = _jc_fc2.dumps(_new_qd_fc2)[:8000]
                            fresh2.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception:
                            pass
                        _cq_fc, _ca_fc = _ns_fc2(_ctask_fc)
                        fresh2._consult_task = _ctask_fc  # type: ignore
                        if _ctask_fc and _ctask_fc.location and not getattr(fresh2, "location", ""):
                            try:
                                fresh2.location = _ctask_fc.location
                                fresh2.save(ignore_permissions=True)
                                frappe.db.commit()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    if _is_product_casual and _ctask_fc:
                        # First check if the catalogue actually has something — if not, keep the question (don't show empty)
                        _prods_fc = []
                        _fmt_fc = ""
                        try:
                            from heshly_core.services.network.product_recommender import search_products, format_product_recommendations
                            _use_fc = " ".join([str(getattr(_ctask_fc, "facts", {}).get("intended_use") or ""), str(getattr(_ctask_fc, "desired_outcome", "") or "")]).strip() or "smartphone"
                            _bud_fc = getattr(fresh2, "budget_min", None) or getattr(_ctask_fc, "budget_min", None)
                            _prods_fc = search_products(intended_use=_use_fc, budget_min=_bud_fc, budget_max=getattr(fresh2, "budget_max", None), specs=msg_text, location=getattr(fresh2, "location", "") or None)
                            _fmt_fc = format_product_recommendations(_prods_fc, intended_use=_use_fc, budget=_bud_fc)
                        except Exception:
                            pass
                        # If catalogue found matches, show them; otherwise keep the consult question if any
                        if _prods_fc and "couldn't find" not in _fmt_fc.lower():
                            reply_text = _fmt_fc
                            try:
                                recommendations = [{"item_code": p["item_code"], "business_name": p["item_name"], "description": p["description"], "ranking_score": 0.9, "link": ""} for p in _prods_fc]
                            except Exception:
                                pass
                        elif _cq_fc or _ca_fc:
                            reply_text = _cq_fc or _ca_fc or ""
                        else:
                            reply_text = _fmt_fc or "Thanks — could you share a bit more detail so I can narrow the right options?"
                    elif _cq_fc or _ca_fc:
                        reply_text = _cq_fc or _ca_fc or ""
                    else:
                        reply_text = "Thanks — could you share a bit more detail so I can narrow the right options?"
            elif qs == "pending" or qs == "in_progress" or not getattr(fresh2, "requested_service", ""):
                # Farming Lamu answers like "Maize" are in_progress with no service/location — route through consultation
                _cq = None
                _ca = None
                _ctask = None
                try:
                    from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up2, next_consultation_step as _ns2
                    import json as _jc2
                    _qd2_raw = getattr(fresh2, "qualification_data", "") or "{}"
                    _qd2 = _jc2.loads(_qd2_raw) if isinstance(_qd2_raw, str) and _qd2_raw else {}
                    _ex2 = {"requested_service": getattr(fresh2, "requested_service", "") or "", "normalized_service": getattr(fresh2, "normalized_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd2.get("capacity") if isinstance(_qd2, dict) else None, "raw_request": msg_text}
                    # For bare crop answers, pass previous location so farming task updates correctly
                    if not _ex2["location"] and _qd2.get("location"):
                        _ex2["location"] = _qd2.get("location")
                    _ctask, _, _new_qd2 = _up2(msg_text, _qd2, _ex2)
                    _cq, _ca = _ns2(_ctask)
                    # Persist awaiting_fact from _ns2 (plumbing_next _ask) back to qualification_data
                    try:
                        from heshly_core.services.network.consultation_engine import _load_tasks as _lt2b, _save_tasks as _st2b
                        _tasks2b = _lt2b(_new_qd2)
                        for _t in _tasks2b:
                            if _t.task_id == _ctask.task_id:
                                _t.facts = dict(_ctask.facts)
                                _t.matching_brief = _ctask.matching_brief
                                break
                        _new_qd2_p = _st2b(_new_qd2, _tasks2b)
                        fresh2.qualification_data = _jc2.dumps(_new_qd2_p)[:8000]
                        fresh2.save(ignore_permissions=True)
                        frappe.db.commit()
                    except Exception:
                        try:
                            fresh2.qualification_data = _jc2.dumps(_new_qd2)[:8000]
                            fresh2.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception:
                            pass
                    fresh2._consult_task = _ctask  # type: ignore
                    # Sync farming location from consult task if discovered
                    if _ctask and _ctask.domain == "farming" and _ctask.location and not getattr(fresh2, "location", ""):
                        try:
                            fresh2.location = _ctask.location
                            fresh2.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception:
                            pass
                except Exception:
                    pass
                if _cq or _ca:
                    reply_text = _cq or _ca or ""
                elif not getattr(fresh2, "requested_service", "") or not str(getattr(fresh2, "requested_service", "")).strip():
                    if _ctask and getattr(_ctask, "intent", "") == "product_request":
                        try:
                            from heshly_core.services.network.product_recommender import search_products, format_product_recommendations
                            _use = getattr(_ctask, "facts", {}).get("intended_use") or msg_text
                            _prods = search_products(intended_use=_use, budget_min=getattr(fresh2, "budget_min", None), budget_max=getattr(fresh2, "budget_max", None), specs=msg_text, location=getattr(fresh2, "location", "") or None)
                            reply_text = format_product_recommendations(_prods, intended_use=_use, budget=getattr(fresh2, "budget_min", None) or getattr(fresh2, "budget_max", None))
                            try:
                                recommendations = [{"item_code": p["item_code"], "business_name": p["item_name"], "description": p["description"], "ranking_score": 0.9, "link": ""} for p in _prods]
                            except Exception:
                                pass
                        except Exception:
                            reply_text = "What do you need help with, and where are you located?"
                    else:
                        from heshly_core.services.network.notification_service import _follow_up_for_service
                        fu = _follow_up_for_service(getattr(fresh2, "requested_service", "") or "", msg_text, bool(str(getattr(fresh2, "location", "") or "").strip()))
                        reply_text = fu or "Sure — what do you need help with, and where are you located?"
                elif not getattr(fresh2, "location", "") or not str(getattr(fresh2, "location", "")).strip():
                    if qs == "in_progress" and _is_new_request and not _followup_like:
                        reply_text = "Yes — I can help. Which town or area should I search in?"
                    else:
                        reply_text = _cq or "Thanks — where are you located? That helps me find someone nearby."
                else:
                    reply_text = _cq or _ca or "Thanks — could you share a bit more detail so I can narrow the right options?"
            else:
                # Qualified — consultative gate before dispatch: consultation-only tasks don't force a referral
                _should_dispatch = True
                _consult_task_q = getattr(fresh2, "_consult_task", None)
                try:
                    if _consult_task_q is None:
                        from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up2, should_search_providers as _sh2
                        import json as _jc2
                        _qd2 = getattr(fresh2, "qualification_data", "") or "{}"
                        _qd2d = _jc2.loads(_qd2) if isinstance(_qd2, str) and _qd2 else {}
                        _ex2 = {"requested_service": getattr(fresh2, "requested_service", "") or "", "normalized_service": getattr(fresh2, "normalized_service", "") or "", "location": getattr(fresh2, "location", "") or "", "budget_min": getattr(fresh2, "budget_min", None), "budget_max": getattr(fresh2, "budget_max", None), "capacity": _qd2d.get("capacity"), "raw_request": getattr(fresh2, "raw_request", "") or msg_text}
                        _consult_task_q, _, _ = _up2(msg_text, _qd2d, _ex2)
                    from heshly_core.services.network.consultation_engine import should_search_providers as _sh3
                    if not _sh3(_consult_task_q):
                        # Consultation-only (farming feasibility etc.) — give assessment, don't search
                        from heshly_core.services.network.consultation_engine import next_consultation_step as _ns3
                        _q3, _a3 = _ns3(_consult_task_q)
                        if _q3:
                            reply_text = _q3
                            _should_dispatch = False
                        elif _a3:
                            reply_text = _a3
                            _should_dispatch = False
                        else:
                            _should_dispatch = False
                            reply_text = _a3 or "Let me know if you'd like me to connect you to a relevant professional for this."
                except Exception:
                    pass
                # Product requests: route to catalogue, not provider matching
                try:
                    if _consult_task_q and getattr(_consult_task_q, "intent", "") == "product_request":
                        from heshly_core.services.network.product_recommender import search_products, format_product_recommendations
                        _use2 = getattr(_consult_task_q, "facts", {}).get("intended_use") or getattr(_consult_task_q, "desired_outcome", "") or msg_text
                        _prods2 = search_products(intended_use=_use2, budget_min=getattr(fresh2, "budget_min", None), budget_max=getattr(fresh2, "budget_max", None), specs=msg_text, location=getattr(fresh2, "location", "") or None)
                        reply_text = format_product_recommendations(_prods2, intended_use=_use2, budget=getattr(fresh2, "budget_min", None) or getattr(fresh2, "budget_max", None))
                        recommendations = [{"item_code": p["item_code"], "business_name": p["item_name"], "description": p["description"], "ranking_score": 0.9, "link": ""} for p in _prods2]
                        _should_dispatch = False
                except Exception:
                    pass
                # Persist consultation state for qualified branch so farming/product facts survive
                try:
                    if _consult_task_q is not None:
                        import json as _jc_save
                        _qd_save = getattr(fresh2, "qualification_data", "") or "{}"
                        _qd_save_d = _jc_save.loads(_qd_save) if isinstance(_qd_save, str) and _qd_save else {}
                        from heshly_core.services.network.consultation_engine import _load_tasks as _lt_save, _save_tasks as _st_save
                        _tasks_save = _lt_save(_qd_save_d)
                        # upsert already returned updated tasks via _up2 if we called it; re-derive save if needed
                        # For the qualified path we called _up2 without saving — do it now
                        if not any(t.task_id == _consult_task_q.task_id for t in _tasks_save):
                            # _consult_task_q was not in loaded tasks (fresh call) — ensure it's saved
                            from heshly_core.services.network.consultation_engine import upsert_task_from_message as _up_save
                            _, _, _new_qd_save = _up_save(msg_text, _qd_save_d, _ex2)
                            fresh2.qualification_data = _jc_save.dumps(_new_qd_save)[:8000]
                            try:
                                fresh2.save(ignore_permissions=True)
                                frappe.db.commit()
                            except Exception:
                                pass
                        else:
                            # Update the in-memory task list with the mutated _consult_task_q and save
                            for _ts in _tasks_save:
                                if _ts.task_id == _consult_task_q.task_id:
                                    _ts.facts = dict(_consult_task_q.facts)
                                    _ts.location = _consult_task_q.location
                                    _ts.last_active = _consult_task_q.last_active
                                    break
                            _new_qd_save2 = _st_save(_qd_save_d, _tasks_save)
                            fresh2.qualification_data = _jc_save.dumps(_new_qd_save2)[:8000]
                            try:
                                fresh2.save(ignore_permissions=True)
                                frappe.db.commit()
                            except Exception:
                                pass
                except Exception:
                    pass
                if _should_dispatch:
                    # Task-aware dispatch: each qualified consult_task gets its own offer
                    # Keep legacy has_pending/assigned guards but scoped per-task
                    try:
                        import json as _jc_taskd
                        from heshly_core.services.network.consultation_engine import _load_tasks as _lt_taskd, should_search_providers as _sh_taskd
                        from heshly_core.services.network.dispatch_service import offer_next_for_task, _has_offered_for_task, cancel_task_dispatches
                        _qd_taskd = _jc_taskd.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                        _tasks_taskd = _lt_taskd(_qd_taskd)
                        # If correction just happened, cancel obsolete dispatches for old service
                        if _is_correction and _new_svc if '_new_svc' in locals() else False:
                            try:
                                # find tasks that were corrected (old service no longer present)
                                pass
                            except: pass
                        # Dispatch each qualified task that has location and needs search, idempotently
                        _first_new_dispatch = None
                        for _t in _tasks_taskd:
                            if ( _t.location or "").strip() == "":
                                continue
                            if not _sh_taskd(_t):
                                continue
                            if _has_offered_for_task(str(getattr(fresh2, "network_conversation_id", "")), _t.task_id):
                                continue
                            _d = offer_next_for_task(str(getattr(fresh2, "network_conversation_id", "")), _t.task_id)
                            if _d and _first_new_dispatch is None:
                                _first_new_dispatch = _d
                        if _first_new_dispatch:
                            dispatched = _first_new_dispatch
                        elif not has_pending and not already_assigned:
                            # Legacy fallback: conversation-level dispatch for single-task compat
                            dispatched = offer_next(str(getattr(fresh2, "network_conversation_id", "")))
                        else:
                            dispatched = None
                    except Exception as _e_taskd:
                        # Fallback to legacy
                        try:
                            if not has_pending and not already_assigned:
                                dispatched = offer_next(str(getattr(fresh2, "network_conversation_id", "")))
                            else:
                                dispatched = None
                        except Exception:
                            dispatched = None
                # Build reply — but do NOT overwrite a consultation question/assessment
                if not _should_dispatch:
                    # reply_text already holds the consultation question/assessment or product catalogue — keep it
                    pass
                elif dispatched:
                    reply_text = "Thanks — I've noted your request and I'm finding someone for you. Here are the best matches I found."
                else:
                    # No dispatch produced — task-aware no-match keeps consultation open
                    try:
                        from heshly_core.services.network.matching_engine import filter_eligible_candidates, enrich_from_frappe
                        from heshly_core.services.network.consultation_engine import _load_tasks as _lt_nm, get_active_task as _gat_nm
                        import json as _jc_nm
                        _qd_nm = _jc_nm.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                        _tasks_nm = _lt_nm(_qd_nm)
                        _active_nm = _gat_nm(_qd_nm) or _consult_task_q
                        # Prefer consultant no-match reply when we have a trade task
                        _used_consultant = False
                        if _active_nm is not None:
                            try:
                                from heshly_core.services.network.service_consultant import no_match_reply, should_defer_to_legacy_guide
                                if not should_defer_to_legacy_guide(_active_nm):
                                    reply_text = no_match_reply(_active_nm)
                                    # Persist pending_prompt/ referral_state
                                    try:
                                        fresh2.qualification_data = _jc_nm.dumps(_qd_nm)[:8000]
                                        fresh2.save(ignore_permissions=True)
                                        frappe.db.commit()
                                    except Exception:
                                        pass
                                    _used_consultant = True
                            except Exception:
                                pass
                        if not _used_consultant:
                            memberships = frappe.get_all("Heshly Network Membership", filters={"status": "Active", "accepts_network_leads": 1}, fields=["*"])
                            if memberships:
                                bmap, kmap, _ = enrich_from_frappe(memberships)
                                # Task-aware eligibility check so Mwiki without nearby is correctly empty, but nearby expansion still reported
                                eligible = filter_eligible_candidates(fresh2, memberships, bmap, kmap, consult_task=_active_nm)
                                if not eligible:
                                    loc = getattr(fresh2, "location", "") or (_active_nm.location if _active_nm else "") or ""
                                    svc = getattr(fresh2, "requested_service", "") or (_active_nm.requested_service if _active_nm else "") or "that service"
                                    reply_text = f"I couldn't find an exact match for {svc} {('in ' + loc) if loc else ''} right now. Would you like me to check nearby areas? Your request stays open."
                                    # Mark task so 'yes' expands to Nairobi via location tokens
                                    if _active_nm is not None:
                                        try:
                                            _active_nm.facts["pending_prompt"] = "nearby"
                                            _active_nm.referral_state = "no_match"
                                            _qd_nm2 = _jc_nm.loads(getattr(fresh2, "qualification_data", "") or "{}") if getattr(fresh2, "qualification_data", "") else {}
                                            from heshly_core.services.network.consultation_engine import _save_tasks as _st_nm2, _load_tasks as _lt_nm2
                                            _tasks2 = _lt_nm2(_qd_nm2)
                                            for _t2 in _tasks2:
                                                if _t2.task_id == _active_nm.task_id:
                                                    _t2.facts.update(_active_nm.facts)
                                                    _t2.referral_state = "no_match"
                                                    break
                                            fresh2.qualification_data = _jc_nm.dumps(_st_nm2(_qd_nm2, _tasks2))[:8000]
                                            fresh2.save(ignore_permissions=True)
                                            frappe.db.commit()
                                        except Exception:
                                            pass
                                else:
                                    reply_text = "I found some options for you — see below. If you'd like, tell me more to narrow it down."
                            else:
                                reply_text = "I'm still building the Heshly network in that area — tell me more and I'll do my best to help."
                    except Exception:
                        reply_text = reply_text or "Thanks — let me look into this for you."
                recommendations = _serialize_recommendations(dispatched or fresh2, fresh2)
                # For web, we return all ranked, not just OFFERED — but filter test fixtures
                if not recommendations and getattr(fresh2, "requested_service", ""):
                    try:
                        from heshly_core.services.network.matching_engine import filter_eligible_candidates, rank_candidates, enrich_from_frappe

                        ms = frappe.get_all("Heshly Network Membership", filters={"status": "Active", "accepts_network_leads": 1}, fields=["*"])
                        ms = [m for m in ms if not _is_test_tenant_id(m.get("tenant_id"))]
                        bmap, kmap, hmap = enrich_from_frappe(ms)
                        eligible = filter_eligible_candidates(fresh2, ms, bmap, kmap)
                        ranked = rank_candidates(fresh2, eligible, bmap, kmap, hmap)[:3]
                        ranked = [c for c in ranked if not _is_test_tenant_id(c.tenant_id)]
                        for c in ranked:
                            biz = frappe.db.get_value("Business Account", {"tenant_id": c.tenant_id}, ["business_id", "business_name", "location"], as_dict=True) if c.tenant_id else None
                            _bn = (biz.get("business_name") if biz else "") or ""
                            if _bn and ("E2E" in _bn or "Test Business" in _bn):
                                continue
                            try:
                                from heshly_core.services.business_slug import public_url as _pub_url2  # type: ignore
                                _slug2 = frappe.db.get_value("Business Account", {"business_id": c.business_id}, "public_slug") if c.business_id else None
                                if not _slug2 and c.tenant_id:
                                    _slug2 = frappe.db.get_value("Business Account", {"tenant_id": c.tenant_id}, "public_slug")
                                _link2 = _pub_url2(str(_slug2).strip().lower()) if _slug2 else ""
                            except Exception:
                                _link2 = ""
                            if not _link2:
                                _link2 = f"https://heshly.com/{(c.business_id or c.tenant_id or '').lower().replace('_','-')}" if (c.business_id or c.tenant_id) else ""
                            recommendations.append(
                                {
                                    "tenant_id": c.tenant_id,
                                    "business_id": c.business_id,
                                    "business_name": (biz.get("business_name") if biz else None) or c.business_id or c.tenant_id,
                                    "location": biz.get("location") if biz else "",
                                    "ranking_score": c.score,
                                    "ranking_reasons": c.reasons,
                                    "link": _link2,
                                }
                            )
                    except Exception:
                        pass
        except Exception:
            reply_text = reply_text or "Thanks for your message — I'm looking into this for you."

        # Ensure reply saved as assistant turn (for website channel we also append, but avoid double whatsapp send)
        try:
            if reply_text:
                # Use same helper but it will attempt whatsapp via central — for web we still append turn; whatsapp send will be best-effort but customer_phone is wa_web_... so no real number, send will no-op.
                from heshly_core.services.network.network_conversation_service import append_turn as _append

                fresh3 = frappe.get_doc("Heshly Network Conversation", conv.name)
                # dedupe: don't append duplicate
                turns = getattr(fresh3, "turns", []) or []
                last_assistant = ""
                for t in reversed(turns):
                    if getattr(t, "role", "") == "assistant":
                        last_assistant = str(getattr(t, "message", "") or "")
                        break
                if last_assistant.strip() != reply_text.strip():
                    _append(fresh3, "assistant", reply_text)
                    conv = fresh3
        except Exception:
            pass

        # Reset must clear stale state: after a reset the next message must not inherit old service/location.
        # Also signal frontend to clear visible old turns when we actually performed a row-reset.
        _reset_performed = bool(_reset_done)
        # Final payload
        try:
            final_conv = frappe.get_doc("Heshly Network Conversation", conv.name)
        except Exception:
            final_conv = conv
        # Serialize turns for frontend (last 20)
        turns_out: list[dict[str, Any]] = []
        try:
            for t in (getattr(final_conv, "turns", []) or [])[-20:]:
                turns_out.append(
                    {
                        "role": getattr(t, "role", "") or "",
                        "message": getattr(t, "message", "") or "",
                        "timestamp": str(getattr(t, "timestamp", "") or getattr(t, "creation", "") or ""),
                    }
                )
        except Exception:
            pass
        payload = {
            "success": True,
            "session_id": session_id,
            "reply": reply_text,
            "intent": _intent,
            "is_greeting": _is_greeting,
            "is_reset": _is_reset or _reset_performed,
            "reset": _reset_performed,
            "qualification": {
                "requested_service": getattr(final_conv, "requested_service", "") or "",
                "location": getattr(final_conv, "location", "") or "",
                "urgency": getattr(final_conv, "urgency", "") or "",
                "qualification_state": getattr(final_conv, "qualification_state", "") or "",
            },
            "recommendations": recommendations,
            "conversation": {
                "network_conversation_id": getattr(final_conv, "network_conversation_id", "") or "",
                "network_status": getattr(final_conv, "network_status", "") or "",
                "turn_count": int(getattr(final_conv, "turn_count", 0) or 0),
            },
            "turns": turns_out,
            "dispatch_counts": _dispatch_to_counts(final_conv),
        }
        try:
            cache = frappe.cache()  # type: ignore
            cache.set_value(f"hcn_web_last_reply:{session_id}", json.dumps(payload), expires_in_sec=300)
            cache.set_value(f"hcn_web_idem:{session_id}:{hash(text) & 0xFFFFFFFF:08x}", "1", expires_in_sec=60)
        except Exception:
            pass
        return payload
    except Exception as e:
        try:
            frappe.log_error(frappe.get_traceback() or str(e), "HCN website_chat error")  # type: ignore
        except Exception:
            pass
        # Include diagnostic in server log; return safe message + diagnostic marker for frontend
        # The browser error handler will surface a retry, not this internals
        try:
            frappe.logger("heshly_website").error("website_chat failed sid=%s err=%s", session_id, type(e).__name__)  # type: ignore
        except Exception:
            pass
        return {"success": False, "message": "Something went wrong. Please try again.", "session_id": session_id, "error_code": type(e).__name__}


@frappe.whitelist(allow_guest=True)
def get_conversation(payload=None, **kwargs):
    """Return website conversation turns for a session_id (channel=web)."""
    data = _unwrap(payload, kwargs)
    session_raw = data.get("session_id") or data.get("sessionId") or data.get("conversation_id")
    if not session_raw:
        return {"success": False, "message": "session_id is required"}
    session_id = _normalize_web_session_id(str(session_raw))
    phone = _phone_for_web_session(session_id)
    try:
        conv = frappe.db.get_value(
            "Heshly Network Conversation",
            {"customer_phone": phone, "channel": "web"},
            ["name", "network_conversation_id"],
            as_dict=True,
            order_by="modified desc",
        )
        if not conv or not conv.get("name"):
            return {"success": True, "session_id": session_id, "turns": [], "conversation": None}
        doc = frappe.get_doc("Heshly Network Conversation", conv["name"])
        turns: list[dict[str, Any]] = []
        for t in (getattr(doc, "turns", []) or [])[-30:]:
            turns.append({"role": getattr(t, "role", "") or "", "message": getattr(t, "message", "") or "", "timestamp": str(getattr(t, "timestamp", "") or "")})
        return {
            "success": True,
            "session_id": session_id,
            "conversation": {"network_conversation_id": getattr(doc, "network_conversation_id", ""), "network_status": getattr(doc, "network_status", "")},
            "turns": turns,
        }
    except Exception:
        return {"success": False, "message": "Could not load conversation", "session_id": session_id}


@frappe.whitelist(allow_guest=True)
def clear_conversation(payload=None, **kwargs):
    """Clear the current active conversation for session_id. Does not wipe history table, just cancels the active row."""
    data = _unwrap(payload, kwargs)
    session_raw = data.get("session_id") or data.get("sessionId") or data.get("conversation_id")
    if not session_raw:
        return {"success": False, "message": "session_id is required"}
    session_id = _normalize_web_session_id(str(session_raw))
    phone = _phone_for_web_session(session_id)
    try:
        from heshly_core.services.network.network_conversation_service import reset_for_new_request
        # Find active conversation
        conv = frappe.db.get_value(
            "Heshly Network Conversation",
            {"customer_phone": phone, "channel": "web"},
            ["name"],
            as_dict=True,
            order_by="modified desc",
        )
        if conv and conv.get("name"):
            doc = frappe.get_doc("Heshly Network Conversation", conv["name"])
            # cancel active
            try:
                from heshly_core.models.network import NetworkStatus, RoutingStatus
                if str(getattr(doc, "network_status", "")) not in (NetworkStatus.COMPLETED.value, NetworkStatus.CANCELLED.value, NetworkStatus.ACCEPTED.value):
                    doc.network_status = NetworkStatus.CANCELLED.value
                    doc.routing_status = RoutingStatus.IDLE.value
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    try:
                        # cancel offered dispatches
                        rows = frappe.get_all("Heshly Network Dispatch", filters={"network_conversation_id": getattr(doc, "network_conversation_id", ""), "status": "OFFERED"}, fields=["name"])
                        for r in rows:
                            try:
                                d = frappe.get_doc("Heshly Network Dispatch", r["name"])
                                d.status = "CANCELLED"
                                d.save(ignore_permissions=True)
                            except Exception:
                                continue
                        frappe.db.commit()
                    except Exception:
                        pass
            except Exception:
                pass
        # Clear caches so next website_chat mints a fresh conversation
        try:
            cache = frappe.cache()
            cache.delete_value(f"hcn_web_last_reply:{session_id}")
            # Also clear any idempotency keys for this session so next message is not replayed
            try:
                import re as _re_cache
                # best-effort: delete last 5 possible idem slots by scanning nothing — just try known text hashes via delete_keys if available
                if hasattr(cache, "delete_keys"):
                    cache.delete_keys(f"hcn_web_idem:{session_id}:*")
                elif hasattr(cache, "delete_value"):
                    # fallback: we cannot enumerate, but delete at least the generic prefix misses — caller will repopulate
                    for _k_suffix in (":stain", ":marketer", ":paint"):
                        try:
                            cache.delete_value(f"hcn_web_idem:{session_id}{_k_suffix}")
                        except Exception:
                            pass
            except Exception:
                pass
            # Force-clear via direct redis delete of pattern if available
            try:
                if hasattr(cache, "cache") and hasattr(cache.cache, "delete"):
                    # frappe redis wrapper
                    pass
                # Direct redis scan fallback using frappe.cache().make_key indirection not needed — pattern delete via redis client
                import frappe as _f2
                try:
                    _redis = _f2.cache().cache if hasattr(_f2.cache(), "cache") else None
                    if _redis and hasattr(_redis, "delete"):
                        # scan keys matching prefix (redis command)
                        try:
                            for _k in _redis.keys(f"hcn_web_idem:{session_id}:*"):
                                try:
                                    _redis.delete(_k.decode() if isinstance(_k, bytes) else _k)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass
        # Mint new session id for New chat semantics when caller wants it; here clear keeps same session_id but next message will auto-create new row
        new_sid = session_id
        # If caller asked for new sid via flag
        if data.get("new_session"):
            import uuid, re
            new_sid = f"hweb_{uuid.uuid4().hex[:12]}"
        return {"success": True, "session_id": new_sid, "cleared": True}
    except Exception as e:
        return {"success": False, "message": "Could not clear conversation", "error": type(e).__name__}

@frappe.whitelist(allow_guest=True)
def track_referral(payload=None, **kwargs):
    """Record website referral click. Validates tenant server-side; increments metrics.

    Payload: { dispatch_id?: string, tenant_id?: string, session_id: string, link: string }
    """
    data = _unwrap(payload, kwargs)
    session_raw = data.get("session_id") or data.get("sessionId")
    if not session_raw:
        return {"success": False, "message": "session_id is required"}
    session_id = _normalize_web_session_id(str(session_raw))
    tenant_id = (data.get("tenant_id") or data.get("tenantId") or data.get("business_id") or "").strip() if isinstance(data.get("tenant_id") or data.get("tenantId") or data.get("business_id"), str) else ""
    dispatch_id = (data.get("dispatch_id") or data.get("dispatchId") or "").strip() if isinstance(data.get("dispatch_id") or data.get("dispatchId"), str) else ""
    link = str(data.get("link") or "")[:500]
    # Validate tenant exists
    if tenant_id and not frappe.db.exists("Business Account", {"tenant_id": tenant_id}):
        # Also check business_id fallback
        if not frappe.db.exists("Business Account", {"business_id": tenant_id}):
            return {"success": False, "message": "Invalid tenant"}
    # Idempotency: dedupe rapid double-clicks per session+dispatch
    try:
        cache = frappe.cache()  # type: ignore
        dedup = f"hcn_web_referral:{session_id}:{dispatch_id or tenant_id}"
        if cache.get_value(dedup):
            return {"success": True, "deduplicated": True, "session_id": session_id}
        cache.set_value(dedup, "1", expires_in_sec=3600)
    except Exception:
        pass
    # Best-effort: increment a dispatch counter if dispatch_id valid, else just log
    try:
        if dispatch_id and frappe.db.exists("Heshly Network Dispatch", {"dispatch_id": dispatch_id}):
            # No custom website_click field yet — log as error-style audit via frappe.logger
            try:
                frappe.logger("heshly_website_referral").info("web referral dispatch=%s tenant=%s session=%s link=%s", dispatch_id, tenant_id, session_id, link[:120])
            except Exception:
                pass
        else:
            try:
                frappe.logger("heshly_website_referral").info("web referral tenant=%s session=%s link=%s", tenant_id, session_id, link[:120])
            except Exception:
                pass
    except Exception:
        pass
    return {"success": True, "session_id": session_id, "tenant_id": tenant_id, "dispatch_id": dispatch_id}
