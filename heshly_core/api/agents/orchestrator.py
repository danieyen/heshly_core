"""Deterministic orchestrator — conditional routing, state ownership, anti-stale.

Shared by n8n (via frappe whitelist) and by website_chat (direct import).
No LLM here — deterministic routing keeps latency/cost low.
Only Reception/Intent agents use LLM where needed via deterministic fallback first.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

import frappe

from heshly_core.api.agents.contracts import validate
from heshly_core.services.network.network_conversation_service import (
    get_or_create_conversation,
    append_turn,
    set_qualification,
)
from heshly_core.services.network.qualification_service import (
    qualify_message,
    classify_customer_intent,
    _extract_open_service,  # type: ignore
)
from heshly_core.services.network.consultation_engine import (
    upsert_task_from_message,
    next_consultation_step,
    should_search_providers,
    get_active_task,
)
from heshly_core.services.network.service_consultant import (
    is_contextual_affirmative,
    is_advice_request,
)
from heshly_core.services.network.matching_engine import filter_eligible_candidates, rank_candidates, enrich_from_frappe
from heshly_core.services.network.dispatch_service import offer_next_for_task


# --- Deterministic helpers ---

GREETING_RE = re.compile(r"^\s*(hi|hello|hey|habari|mambo|good\s+(morning|afternoon|evening))\b", re.I)
DISSATISFACTION_RE = re.compile(r"you\s+are\s+not\s+helping|are\s+not\s+helping|you\s+don'?t\s+need\s+to\s+repeat|are\s+you\s+helping|don'?t\s+repeat|not\s+helping", re.I)
CORRECTION_RE = re.compile(r"\bactually\b|\bno\s+not\s+a\b|\bforget\s+.*previous\b|\bmake\s+that\b|\bchange\s+to\b", re.I)


def _is_greeting(text: str) -> bool:
    return bool(GREETING_RE.match((text or "").strip()))

def _is_dissatisfaction(text: str) -> bool:
    return bool(DISSATISFACTION_RE.search(text or ""))

def _is_correction(text: str) -> bool:
    return bool(CORRECTION_RE.search((text or "").lower()))


def _deterministic_intent(text: str, previous_service: str | None = None) -> dict[str, Any]:
    """Deterministic intent without LLM. Returns intent contract payload."""
    t = (text or "").strip()
    low = t.lower()
    if _is_greeting(t) and len(t.split()) <= 4:
        return {"intent": "GREETING", "confidence": 0.95, "is_correction": False, "is_dissatisfaction": False, "raw_text": t, "entities": {}}
    if _is_dissatisfaction(t):
        return {"intent": "DISSATISFACTION", "confidence": 0.90, "is_correction": False, "is_dissatisfaction": True, "raw_text": t, "entities": {}}
    if _is_correction(t):
        svc = _extract_open_service(t, None) if _extract_open_service else None
        return {"intent": "CORRECTION", "confidence": 0.88, "is_correction": True, "is_dissatisfaction": False, "raw_text": t, "entities": {"service": svc}}
    # Use existing classifier as fallback — already deterministic
    cls = classify_customer_intent(t, previous_service)
    mapping = {
        "reset": "RESET", "correction": "CORRECTION", "frustration": "DISSATISFACTION",
        "new_request": "SERVICE_REQUEST", "continuation": "SERVICE_REQUEST",
        "casual": "OTHER", "greeting": "GREETING"
    }
    mapped = mapping.get(cls, "OTHER")
    # Pest / water-heater etc should not go OTHER
    if mapped == "OTHER" and t:
        # If service extractor finds something, it's a service request
        svc2 = _extract_open_service(t, previous_service) if _extract_open_service else None
        if svc2:
            mapped = "SERVICE_REQUEST"
        elif re.search(r"water\s*heater|geyser|pest|rats?|termites?|cockroaches|plumb|toilet|leak|heater|ac\b|hvac|roof|paint", low):
            mapped = "SERVICE_REQUEST"
    return {"intent": mapped, "confidence": 0.75 if mapped != "OTHER" else 0.55, "is_correction": mapped == "CORRECTION", "is_dissatisfaction": mapped == "DISSATISFACTION", "raw_text": t, "entities": {"service": _extract_open_service(t, previous_service) if _extract_open_service else None}}


def _deterministic_domain(text: str, requested_service: str = "") -> dict[str, Any]:
    from heshly_core.services.network.consultation_engine import _detect_domain
    domain, _ = _detect_domain(text, requested_service)
    # Normalize to contract enum
    mapping = {"water_heater": "water_heater", "pest_control": "pest_control", "general_service": "general", "general": "general"}
    norm = mapping.get(domain, domain)
    if norm not in {"plumbing","electrical","hvac","pest_control","cleaning","general_repairs","water_heater","roofing","painting","general"}:
        norm = "general"
    return {"domain": norm, "confidence": 0.8, "reason": f"pattern:{domain}"}


def _idempotency_key(session_id: str, message_id: str, text: str) -> str:
    import hashlib
    h = hashlib.sha256(f"{session_id}:{message_id}:{text}".encode()).hexdigest()[:16]
    return f"hcn_idem:{h}"


def orchestrate(
    session_id: str,
    message_id: str,
    text: str,
    channel: str = "web",
    tenant_id: str | None = None,
    business_id: str | None = None,
    customer_name: str | None = None,
    phone_number: str | None = None,
    phone_number_id: str | None = None,
) -> dict[str, Any]:
    """Deterministic orchestration. Returns validated orchestrator output.

    - Owns shared state via Frappe network_conversation_service (no stale overwrite).
    - Validates each specialist output before forwarding.
    - Does NOT send to customer — caller must invoke delivery workflow.
    """
    text = (text or "").strip()
    if not text:
        return {"error": "empty message", "response": "Please send a message.", "intent": "OTHER", "domain": "general", "qualification_state": "pending", "delivery_status": "pending"}

    # Normalize session -> phone
    from heshly_core.api.website_chat import _phone_for_web_session, _normalize_web_session_id  # type: ignore
    from heshly_core.api.agents.contracts import ORCHESTRATOR_OUTPUT_SCHEMA

    # Resolve phone per channel
    if channel == "whatsapp" and phone_number:
        phone = str(phone_number).strip()
        ch = "whatsapp"
    else:
        sid = _normalize_web_session_id(session_id) if session_id else _normalize_web_session_id(None)
        session_id = sid
        phone = _phone_for_web_session(sid)
        ch = "web"

    try:
        cache = frappe.cache()  # type: ignore
    except Exception:
        cache = None

    # --- Idempotency: different message_ids with same text are distinct; same id+text is duplicate ---
    idem_key = _idempotency_key(session_id, message_id, text) if message_id else None
    if idem_key and cache:
        prev = cache.get_value(idem_key)
        if prev:
            try:
                return json.loads(prev) if isinstance(prev, str) else prev
            except Exception:
                pass

    conv = get_or_create_conversation(
        customer_phone=phone,
        customer_name=customer_name or "Customer",
        source_phone_number_id=phone_number_id,
        channel=ch,
    )

    # Stale guard: if a newer turn already exists with same message_id, return its response
    try:
        qd_raw = getattr(conv, "qualification_data", "") or "{}"
        qd = json.loads(qd_raw) if isinstance(qd_raw, str) and qd_raw.strip() else (qd_raw if isinstance(qd_raw, dict) else {})
        last_mid = (qd.get("last_message_id") or "") if isinstance(qd, dict) else ""
        last_rid = (qd.get("last_response_id") or "") if isinstance(qd, dict) else ""
        if last_mid and message_id and last_mid == message_id and last_rid:
            # Exact retry — return cached response by idempotency key if available, else fetch last assistant turn
            if idem_key and cache:
                cached = cache.get_value(idem_key)
                if cached:
                    try:
                        return json.loads(cached) if isinstance(cached, str) else cached
                    except Exception:
                        pass
    except Exception:
        pass

    prev_service = str(getattr(conv, "requested_service", "") or "")

    # --- Deterministic specialists via Frappe modules (conditional, not 9-way fan-out) ---
    # Intent specialist performs real classification (same deterministic logic, but via module)
    try:
        from heshly_core.api.agents import intent as intent_mod
        intent_out = intent_mod.handle(text=text, previous_service=prev_service)
    except Exception:
        intent_out = _deterministic_intent(text, prev_service)
    ok, err = validate("intent", intent_out)
    if not ok:
        intent_out = {"intent": "OTHER", "confidence": 0.5, "is_correction": False, "is_dissatisfaction": False, "raw_text": text, "entities": {}}

    # Dissatisfaction / greeting short-circuit via Reception specialist (no matching, no qualification) ---
    if intent_out.get("is_dissatisfaction"):
        try:
            from heshly_core.api.agents import reception as reception_mod
            r = reception_mod.handle(text=text)
            # Reception returns generic, but for dissatisfaction we want the empathetic response
            response = "Sorry about that — I wasn't trying to repeat you. Let's get back to your original request. What would you like me to do next?"
        except Exception:
            response = "Sorry about that — I wasn't trying to repeat you. Let's get back to your original request. What would you like me to do next?"
        # Append turns but do NOT overwrite qualification
        try:
            append_turn(conv, "user", text)
            append_turn(conv, "assistant", response)
            # Persist last ids
            fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
            try:
                qd2 = json.loads(getattr(fresh, "qualification_data", "") or "{}") if getattr(fresh, "qualification_data", "") else {}
            except Exception:
                qd2 = {}
            qd2["last_message_id"] = message_id or str(uuid.uuid4().hex[:12])
            qd2["last_response_id"] = str(uuid.uuid4().hex[:12])
            fresh.qualification_data = json.dumps(qd2)[:8000]
            fresh.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
        out = {"response": response, "intent": "DISSATISFACTION", "domain": "general", "qualification_state": getattr(conv, "qualification_state", "pending"), "delivery_status": "pending", "candidates": []}
        if idem_key and cache:
            try:
                cache.set_value(idem_key, json.dumps(out), expires_in_sec=86400)
            except Exception:
                pass
        return out

    if intent_out.get("intent") == "GREETING" and not prev_service:
        try:
            from heshly_core.api.agents import reception as reception_mod
            response = reception_mod.handle(text=text).get("response") or "Hello! How can I help you today?"
        except Exception:
            response = "Hello! How can I help you today?"
        try:
            append_turn(conv, "user", text)
            append_turn(conv, "assistant", response)
            fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
            qd2 = json.loads(getattr(fresh, "qualification_data", "") or "{}") if getattr(fresh, "qualification_data", "") else {}
            qd2["last_message_id"] = message_id or str(uuid.uuid4().hex[:12])
            qd2["last_response_id"] = str(uuid.uuid4().hex[:12])
            fresh.qualification_data = json.dumps(qd2)[:8000]
            fresh.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass
        out = {"response": response, "intent": "GREETING", "domain": "general", "qualification_state": "pending", "delivery_status": "pending", "candidates": []}
        if idem_key and cache:
            try:
                cache.set_value(idem_key, json.dumps(out), expires_in_sec=86400)
            except Exception:
                pass
        return out

    # --- Qualification (deterministic) ---
    # Load existing qualification
    try:
        existing = json.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
        if not isinstance(existing, dict):
            existing = {}
    except Exception:
        existing = {}

    # Handle correction: replace service, keep location only if still relevant
    if intent_out.get("is_correction") or intent_out.get("intent") == "CORRECTION":
        svc_new = (intent_out.get("entities", {}) or {}).get("service")
        # Intent may have null service (e.g. toilet extraction needs qualification); extract from current message
        if not svc_new:
            try:
                from heshly_core.services.network.qualification_service import _extract_open_service as _eos2, _strip_correction_prefix as _strip2
                candidate = _strip2(text)
                svc_new = _eos2(candidate or text, None)
            except Exception:
                svc_new = None
        if svc_new:
            prev_svc = existing.get("requested_service") or ""
            existing["requested_service"] = svc_new
            # Correction creates a NEW task: clear stale legal task and force new domain task
            is_stale = any(task.get("domain") in ("legal", "general_consult", "general") for task in (existing.get("consult_tasks") or []))
            if prev_svc.lower() != svc_new.lower() or is_stale:
                remaining = [task for task in (existing.get("consult_tasks") or []) if task.get("domain") not in ("legal", "general_consult", "general")]
                existing["consult_tasks"] = remaining
                existing["active_task_id"] = remaining[0]["task_id"] if remaining else None
                if not remaining:
                    existing["requested_service"] = svc_new

    # Normal qualification — for correction, use the cleared `existing` (which has no stale legal task)
    is_corr = intent_out.get("is_correction") or intent_out.get("intent") == "CORRECTION"
    qd_for_qualify = existing if (is_corr or existing.get("consult_tasks")) else existing
    qualified = qualify_message(text, qd_for_qualify if qd_for_qualify.get("consult_tasks") or is_corr else existing)
    # For correction, ensure qualified does not retain stale legal consult_tasks (qualify_message may keep them)
    if is_corr:
        try:
            q_stale = [t for t in (qualified.get("consult_tasks") or []) if isinstance(t, dict) and t.get("domain") in ("legal", "general_consult", "general")]
            if q_stale:
                qualified["consult_tasks"] = [t for t in (qualified.get("consult_tasks") or []) if t not in q_stale]
                if not qualified.get("consult_tasks"):
                    qualified.pop("active_task_id", None)
        except Exception:
            pass
    # Ensure we preserve message_id tracking
    msg_id = message_id or str(uuid.uuid4().hex[:12])
    resp_id = str(uuid.uuid4().hex[:12])

    # Consultation task
    from heshly_core.services.network.qualification_service import _extract_location_value  # type: ignore
    ex = {
        "requested_service": qualified.get("requested_service") or prev_service or "",
        "location": qualified.get("location") or "",
        "budget_min": qualified.get("budget_min"),
        "budget_max": qualified.get("budget_max"),
        "capacity": qualified.get("capacity"),
        "raw_request": text,
    }
    # For correction, force requested_service to the corrected plumbing value if extraction succeeded
    if is_corr and (existing.get("requested_service") or ""):
        # trust the corrected existing service over prev_service fallback
        ex["requested_service"] = existing.get("requested_service") or ex["requested_service"]
    qd_tasks = qualified if isinstance(qualified, dict) else {}
    # If correction and qualified still has stale, use existing (cleared) as base for upsert
    upsert_base = qualified
    if is_corr and existing.get("consult_tasks") is not None and len(existing.get("consult_tasks") or []) == 0 and len(qualified.get("consult_tasks") or []) > 0:
        upsert_base = existing.copy()
        upsert_base.update({"requested_service": ex["requested_service"], "location": ex["location"]})
    ct, tasks_list, new_qd = upsert_task_from_message(text, upsert_base, ex)
    q, _ = next_consultation_step(ct) if ct else (None, None)
    # Merge ct facts (awaiting_fact etc mutated by next_consultation_step) back into new_qd
    if ct and q:
        try:
            from heshly_core.services.network.consultation_engine import _load_tasks, _save_tasks
            _tasks = _load_tasks(new_qd)
            for _t in _tasks:
                if _t.task_id == ct.task_id:
                    _t.facts = dict(ct.facts)
                    _t.matching_brief = ct.matching_brief or _t.matching_brief
                    break
            new_qd = _save_tasks(new_qd, _tasks)
        except Exception:
            pass

    # Persist qualification + tasks via canonical service (owns state)
    try:
        fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
        # Merge via set_qualification then manual tasks merge
        set_qualification(fresh, qualified)
        # Overwrite qualification_data with task-enriched version
        try:
            merged_qd = json.loads(getattr(fresh, "qualification_data", "") or "{}") if getattr(fresh, "qualification_data", "") else {}
        except Exception:
            merged_qd = {}
        merged_qd.update(new_qd)
        merged_qd["last_message_id"] = msg_id
        merged_qd["last_response_id"] = resp_id
        # Persist facts from ct if any (awaiting_fact etc)
        fresh.qualification_data = json.dumps(merged_qd)[:8000]
        fresh.save(ignore_permissions=True)
        frappe.db.commit()
        conv = fresh
    except Exception as e:
        frappe.log_error(frappe.get_traceback() or str(e), "orchestrator persist failed")  # type: ignore

    # Append user turn
    try:
        append_turn(conv, "user", text)
    except Exception:
        pass

    # Domain — preserve active task domain for location-only continuations
    _active_for_domain = None
    try:
        _active_for_domain = get_active_task(qd_tasks) if isinstance(qd_tasks, dict) else None
    except Exception:
        pass
    # If active task exists and message looks like a location, keep its domain
    _use_prev_domain = False
    if _active_for_domain and ex.get("location") and not _extract_open_service(text, prev_service):
        _use_prev_domain = True
    if _use_prev_domain:
        domain_out = {"domain": _active_for_domain.domain, "confidence": 0.9, "reason": "continuation:location"}
    else:
        domain_out = _deterministic_domain(text, ex.get("requested_service") or "")
        ok, _ = validate("domain", domain_out)
        if not ok:
            domain_out = {"domain": "general", "confidence": 0.5, "reason": "fallback"}

    # Qualification next question vs matching
    # If consultation asks a question, that's the response — no matching yet
    if q:
        response = q
        qual_state = getattr(conv, "qualification_state", "in_progress")
        out = {"response": response, "intent": intent_out["intent"], "domain": domain_out["domain"], "qualification_state": qual_state, "delivery_status": "pending", "candidates": [], "chosen_business_id": None}
        try:
            append_turn(conv, "assistant", response)
            if idem_key and cache:
                cache.set_value(idem_key, json.dumps(out), expires_in_sec=86400)
        except Exception:
            pass
        return out

    # Otherwise, try matching (deterministic, grounded)
    candidates: list[dict] = []
    chosen = None
    try:
        if should_search_providers(ct) if ct else False:
            # Use existing matching
            try:
                from heshly_core.services.network.matching_engine import filter_eligible_candidates, rank_candidates, enrich_from_frappe
                # Enrich needs frappe memberships — reuse existing path via offer_next_for_task if qualified and has location
                if getattr(conv, "location", "") or (ct and ct.location):
                    disp = offer_next_for_task(str(getattr(conv, "network_conversation_id", "")), ct.task_id if ct else None)
                    if disp:
                        candidates = [{"business_id": getattr(disp, "business_id", ""), "score": getattr(disp, "ranking_score", 0)}]
                        chosen = candidates[0]
                        response = f"I found a suitable provider for {ex.get('requested_service') or domain_out['domain']}."
                    else:
                        response = "I couldn't find a suitable provider for that request right now. Would you like me to check nearby areas?"
                else:
                    response = "Thanks — could you share your location so I can find providers nearby?"
            except Exception:
                response = "Thanks — could you share your location so I can find providers nearby?"
        else:
            # Not ready for search — use next question if any else generic
            response = q or "Thanks for the detail — could you share a bit more so I can find the most suitable option?"
    except Exception as e:
        response = "Thanks for your message — could you share a bit more detail?"
        frappe.log_error(str(e), "orchestrator matching failed")  # type: ignore

    # Final response validation
    ok, err = validate("response", {"response": response})
    if not ok:
        response = "Thanks for your message — how can I help further?"

    # Persist assistant turn
    try:
        append_turn(conv, "assistant", response)
        if idem_key and cache:
            out = {"response": response, "intent": intent_out["intent"], "domain": domain_out["domain"], "qualification_state": getattr(conv, "qualification_state", "pending"), "delivery_status": "pending", "candidates": candidates, "chosen_business_id": (chosen or {}).get("business_id")}
            cache.set_value(idem_key, json.dumps(out), expires_in_sec=86400)
    except Exception:
        pass

    # Attach delivery metadata for J
    return {
        "response": response,
        "intent": intent_out["intent"],
        "domain": domain_out["domain"],
        "qualification_state": getattr(conv, "qualification_state", "pending"),
        "delivery_status": "pending",
        "candidates": candidates,
        "chosen_business_id": (chosen or {}).get("business_id") if chosen else None,
        "session_id": session_id,
        "message_id": msg_id,
        "response_id": resp_id,
        "phone": phone,
        "channel": ch,
        "tenant_id": tenant_id,
    }


@frappe.whitelist(allow_guest=True)
def orchestrate_api(**kwargs):
    """Frappe whitelist wrapper for n8n orchestrator workflow."""
    session_id = kwargs.get("session_id") or kwargs.get("sessionId") or kwargs.get("conversation_id") or ""
    message_id = kwargs.get("message_id") or kwargs.get("messageId") or kwargs.get("wamid") or ""
    text = kwargs.get("text") or kwargs.get("message") or kwargs.get("current_message") or ""
    channel = kwargs.get("channel") or ("whatsapp" if kwargs.get("phone_number") else "web")
    result = orchestrate(
        session_id=str(session_id or ""),
        message_id=str(message_id or ""),
        text=str(text or ""),
        channel=str(channel or "web"),
        tenant_id=kwargs.get("tenant_id"),
        business_id=kwargs.get("business_id"),
        customer_name=kwargs.get("customer_name"),
        phone_number=kwargs.get("phone_number"),
        phone_number_id=kwargs.get("phone_number_id"),
    )
    return result


@frappe.whitelist(allow_guest=True)
def health():
    return {"success": True, "orchestrator": "ok"}
