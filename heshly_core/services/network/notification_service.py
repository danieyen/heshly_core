"""Network notifications — concise business summaries, seamless customer messages."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from heshly_core.services.network.settings_service import get_network_settings


def _fmt_deadline(deadline: Any) -> str:
    try:
        if isinstance(deadline, str):
            return deadline
        dt = deadline
        if dt and getattr(dt, "tzinfo", None) is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.strftime("%H:%M %Z") if dt else "5 minutes"
    except Exception:
        return "5 minutes"


def business_summary_text(dispatch: Any, conversation: Any) -> str:
    service = getattr(conversation, "requested_service", "") or "General inquiry"
    location = getattr(conversation, "location", "") or "Not specified"
    urgency = getattr(conversation, "urgency", "medium") or "medium"
    preferred = getattr(conversation, "preferred_time", "") or "Flexible"
    phone = getattr(conversation, "customer_phone", "") or ""
    name = getattr(conversation, "customer_name", "") or "Customer"
    budget_min = getattr(conversation, "budget_min", None)
    budget_max = getattr(conversation, "budget_max", None)
    budget_str = ""
    if budget_min is not None or budget_max is not None:
        budget_str = f"\nBudget: {budget_min or '—'} – {budget_max or '—'}"
    deadline = _fmt_deadline(getattr(dispatch, "deadline_at", None))
    score = getattr(dispatch, "ranking_score", None)
    return (
        f"🔔 New Heshly Network opportunity\n\n"
        f"Customer: {name} ({phone})\n"
        f"Service: {service}\n"
        f"Location: {location}\n"
        f"Urgency: {urgency}\n"
        f"Preferred time: {preferred}{budget_str}\n"
        f"Match score: {score if score is not None else '—'}\n\n"
        f"Please ACCEPT or DECLINE before {deadline}.\n"
        f"If you don't respond, the lead will be offered to the next business.\n"
        f"View details in your Heshly portal → Network Leads."
    )


def notify_business(dispatch: Any, conversation: Any) -> None:
    """Send WhatsApp/in-app notification to the business (best-effort)."""
    text = business_summary_text(dispatch, conversation)
    # increment offered counter
    try:
        import frappe  # type: ignore
        tid = getattr(dispatch, "tenant_id", "")
        m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tid}, ["name"], as_dict=False)
        if m:
            frappe.db.sql("UPDATE `tabHeshly Network Membership` SET total_leads_offered = COALESCE(total_leads_offered,0)+1 WHERE name=%s", (m,))
            frappe.db.commit()
    except Exception:
        pass
    # WhatsApp send is optional — portal notification is primary for MVP.
    # Attempt WhatsApp via tenant's own number if configured (non-blocking).
    try:
        import frappe  # type: ignore
        from heshly_core.services.whatsapp.outgoing_message_sender import WhatsAppOutgoingMessageSender  # type: ignore
        tid = getattr(dispatch, "tenant_id", "")
        # find tenant's primary WhatsApp number to lookup recipient? For MVP, skip actual WhatsApp to business phone
        # and rely on portal + optional email. Keep hook for future.
        _ = text  # keep linter quiet
    except Exception:
        pass


def notify_timeout(previous_tenant_id: str, conversation: Any) -> None:
    try:
        # portal notification only for MVP
        pass
    except Exception:
        pass


def _redact_phone(phone: str) -> str:
    """Redact middle digits: 2547******29"""
    p = (phone or "").strip()
    if len(p) <= 6:
        return "***"
    return p[:4] + "***" + p[-3:]


def _send_whatsapp_via_central(customer_phone: str, text: str) -> bool:
    """Best-effort outbound via central Heshly number using existing sender. Never raises.
    Logs ONLY redacted phone, phone_number_id, config ID/name, HTTP status, Meta error, returned ID — never tokens.
    """
    try:
        import frappe  # type: ignore
        settings = get_network_settings()
        phone_number_id = (getattr(settings, "central_phone_number_id", "") or "").strip()
        cfg_id = (getattr(settings, "central_configuration_id", "") or "").strip()
        if not phone_number_id or not cfg_id:
            try:
                frappe.logger("heshly_whatsapp_router").warning("layer2 outbound missing config phone_number_id=%s cfg_id=%s to=%s", phone_number_id or "MISSING", cfg_id or "MISSING", _redact_phone(customer_phone))
            except Exception:
                pass
            return False
        # Reuse existing repository + sender stack — repository decrypts Password fields via get_password
        from heshly_core.repositories.whatsapp_configuration_repository import WhatsAppConfigurationRepository
        repo = WhatsAppConfigurationRepository()
        cfg = repo.get_by_phone_number_id(phone_number_id)
        if not cfg:
            # fallback to cfg_id
            cfg = repo.get_by_configuration_id(cfg_id)
        if not cfg or not (getattr(cfg, "phone_number_id", "") or "").strip():
            try:
                frappe.logger("heshly_whatsapp_router").warning("layer2 outbound config not found phone_number_id=%s cfg_id=%s to=%s", phone_number_id, cfg_id, _redact_phone(customer_phone))
            except Exception:
                pass
            return False
        # Ensure phone_number_id matches central (log mismatch but still proceed)
        if str(cfg.phone_number_id).strip() != phone_number_id:
            try:
                frappe.logger("heshly_whatsapp_router").warning("layer2 outbound phone_number_id mismatch config=%s vs central=%s to=%s", str(cfg.phone_number_id).strip(), phone_number_id, _redact_phone(customer_phone))
            except Exception:
                pass
        # Validate token is not masked stars
        tok = getattr(cfg, "access_token", "") or ""
        if "****" in tok or tok.strip().startswith("*") or len(tok) < 20:
            try:
                frappe.logger("heshly_whatsapp_router").error("layer2 outbound access_token appears masked or invalid phone_number_id=%s cfg_id=%s to=%s token_len=%s", phone_number_id, getattr(cfg, "configuration_id", ""), _redact_phone(customer_phone), len(tok))
            except Exception:
                pass
            return False
        # Build message — to MUST be customer phone, not Heshly number
        to_phone = customer_phone.strip().replace(" ", "").replace("+", "")
        # Ensure E164 without plus but digits only; WhatsApp expects digits (Meta accepts with or without + but we normalize)
        # Keep as digits; if starts with 0, keep as-is (should not happen for Kenya 254)
        from heshly_core.models.whatsapp import WhatsAppContact, WhatsAppDirection, WhatsAppMessage, WhatsAppMessageType
        msg = WhatsAppMessage(
            message_id="",
            conversation_id=f"{cfg.tenant_id}:{to_phone}" if getattr(cfg, "tenant_id", "") else to_phone,
            contact=WhatsAppContact(phone_number=to_phone),
            direction=WhatsAppDirection.OUTBOUND,
            message_type=WhatsAppMessageType.TEXT,
            text=text,
        )
        from heshly_core.services.whatsapp.whatsapp_manager import WhatsAppManager
        mgr = WhatsAppManager()
        result = mgr.send_message(cfg, msg)
        # Structured outbound logging — never log tokens
        try:
            from heshly_core.services.whatsapp.api.api_models import CloudAPISuccess, CloudAPIError
            cfg_name = getattr(cfg, "configuration_id", "") or cfg_id
            redacted = _redact_phone(to_phone)
            if isinstance(result, CloudAPISuccess):
                # success: log phone_number_id, config, HTTP-like success, returned Meta message ID
                meta_id = getattr(result, "message_id", "") or ""
                # Extract HTTP status from metadata if present, else infer 200
                status = 200
                try:
                    if isinstance(result.metadata, dict) and "error" in result.metadata:
                        status = 400
                except Exception:
                    pass
                frappe.logger("heshly_whatsapp_router").info("layer2 outbound SUCCESS phone_number_id=%s config=%s to=%s http_status=%s meta_message_id=%s", phone_number_id, cfg_name, redacted, status, (meta_id[:20] + "***" if meta_id else "MISSING"))
                if not meta_id:
                    frappe.logger("heshly_whatsapp_router").warning("layer2 outbound success but missing Meta message ID phone_number_id=%s config=%s to=%s", phone_number_id, cfg_name, redacted)
            elif isinstance(result, CloudAPIError):
                frappe.logger("heshly_whatsapp_router").error("layer2 outbound META ERROR phone_number_id=%s config=%s to=%s http_status=%s code=%s type=%s message=%s", phone_number_id, cfg_name, redacted, "error", getattr(result, "code", ""), getattr(result, "error_type", ""), (getattr(result, "message", "") or "")[:300])
            else:
                frappe.logger("heshly_whatsapp_router").warning("layer2 outbound unknown result phone_number_id=%s config=%s to=%s result_type=%s", phone_number_id, cfg_name, redacted, type(result).__name__)
        except Exception:
            # fallback minimal log
            try:
                frappe.logger("heshly_whatsapp_router").info("layer2 outbound central phone_number_id=%s to=%s ok=%s", phone_number_id, _redact_phone(to_phone), bool(result))
            except Exception:
                pass
        from heshly_core.services.whatsapp.api.api_models import CloudAPISuccess as _CAS
        return isinstance(result, _CAS)
    except Exception as e:
        try:
            import frappe as _f  # type: ignore
            _f.logger().warning(f"layer2 outbound failed: {e}")
        except Exception:
            pass
        return False


def _should_greet(user_text: str, conv: Any) -> bool:
    if not user_text:
        return False
    low = user_text.strip().lower()
    if low in ("hi", "hello", "hey", "hie", "habari", "mambo", "sasa", "niaje", "yo", "helo", "heyy", "hii", "hiii", "salama", "poa"):
        return True
    if len(user_text.strip()) <= 15 and any(w in low for w in ("hi", "hello", "hey", "habari", "mambo")):
        return True
    try:
        if getattr(conv, "turn_count", 0) <= 2 and not getattr(conv, "requested_service", ""):
            from heshly_core.services.network.qualification_service import qualify_message
            q = qualify_message(user_text, {})
            if not q.get("requested_service") and not q.get("location") and q.get("qualification_state") == "pending":
                return True
    except Exception:
        pass
    return False


def _is_safe_service_token_for_template(service: str | None) -> bool:
    """Only allow a normalized, short category token before `provider`/`service`."""
    import re as _re
    s = (service or "").strip()
    if not s or s == "__prohibited__":
        return False
    low = s.lower()
    if _re.search(r"\b(?:need someone|inspect a crack|the wall of|my house|can you help)\b", low):
        return False
    if len(s.split()) > 3 or len(s) > 35:
        return False
    return bool(_re.match(r"^[A-Za-z][A-Za-z\s/-]{1,30}$", s))


def _effective_service_for_reply(conv_or_service: Any, raw_fallback: str = "") -> str | None:
    """Resolve effective safe service: prefer normalized_service/provider_category when safe."""
    try:
        # If a conv object was passed, prefer its normalized/provider/requested in order
        if not isinstance(conv_or_service, str):
            for attr in ("normalized_service", "provider_category", "requested_service"):
                v = str(getattr(conv_or_service, attr, "") or "").strip()
                if v and _is_safe_service_token_for_template(v):
                    return v
            # Fall back to raw of the conv
            raw_conv = str(getattr(conv_or_service, "raw_request", "") or "").strip()
            if raw_conv:
                from heshly_core.services.network.qualification_service import _normalize_professional_request
                norm, _ = _normalize_professional_request(raw_conv)
                if norm and _is_safe_service_token_for_template(norm):
                    return norm
        else:
            svc = str(conv_or_service or "").strip()
            if svc and _is_safe_service_token_for_template(svc):
                return svc
        raw = str(raw_fallback or "").strip()
        if raw:
            from heshly_core.services.network.qualification_service import _normalize_professional_request
            norm, _ = _normalize_professional_request(raw)
            if norm and _is_safe_service_token_for_template(norm):
                return norm
    except: pass
    return None


def _follow_up_for_service(requested_service: str | None, raw_user_text: str, location_present: bool) -> str | None:
    """Human receptionist follow-ups — template-safe: never interpolate raw user text."""
    from heshly_core.services.network.qualification_service import _is_prohibited
    txt = (raw_user_text or "").strip()
    txt_low = txt.lower()
    if _is_prohibited(txt):
        return "Sorry, I can't help with that request."
    svc = (requested_service or "").strip()
    svc_low = svc.lower()
    # Normalize raw-like services like "inspect a crack" via effective service before safety gate
    if svc and not _is_safe_service_token_for_template(svc):
        eff = _effective_service_for_reply(None, txt)
        if eff and _is_safe_service_token_for_template(eff):
            svc = eff
            svc_low = svc.lower()
        else:
            # Still allow inspection/building via txt inference when location missing
            if any(k in txt_low for k in ("crack", "wall", "building", "structural", "roof")) and not location_present:
                return "Absolutely. I can help you find the right professional for that. What area is the property in?"
            return None if location_present else "Sure — where are you located?"
    if not svc_low or svc_low == "__prohibited__":
        return None
    if svc_low in ("plumbing", "plumber"):
        if len(txt_low.split()) > 6 and any(w in txt_low for w in ("leak", "blocked", "drain", "tap", "pipe", "toilet", "sink", "burst")):
            return "Got it — let me find someone for you."
        return "Sure, I can help you find one. What's the plumbing issue?"
    if svc_low in ("vet", "veterinary", "veterinarian"):
        if any(w in txt_low for w in ("dog", "cat", "cow", "goat", "chicken", "animal", "pet", "sick", "vomit", "not eating", "injured")):
            return "Sorry to hear that — what seems to be the issue?"
        return "Sure, I can help with that. What do you need the vet for?"
    if svc_low in ("dental", "dentist"):
        if any(w in txt_low for w in ("pain", "extraction", "cleaning", "braces", "whitening", "check", "cavity", "ache")):
            return "Got it — is it urgent or can it wait a few days?"
        return "Of course. Are you looking for a general check-up, or is there a specific problem?"
    if "architect" in svc_low or "inspection" in svc_low or "building" in svc_low or "roof" in svc_low:
        return "Absolutely. I can help you find the right professional for that. What area is the property in?"
    if not location_present:
        return "Sure — where are you located?"
    if any(w in txt_low for w in ("urgent", "today", "tomorrow", "asap", "now", "emergency")):
        return "Thanks — let me find someone for you."
    if "cctv" in svc_low or "camera" in svc_low:
        if any(w in txt_low for w in ("shop", "home", "farm", "office")):
            return "Thanks — let me find someone for you."
        return "Sure — is it for a shop, home, or something else?"
    if "fridge" in svc_low or "appliance" in svc_low:
        if any(w in txt_low for w in ("cooling", "cold", "not working", "sick")):
            return "Thanks — let me find someone for you."
        return "Sure — what's the issue with it?"
    if "solar" in svc_low:
        if any(w in txt_low for w in ("farm", "shop", "home", "design", "install")):
            return "Thanks — let me find someone for you."
        return "Sure — is it for a home, shop, or farm?"
    if "borehole" in svc_low:
        return "Sure — is it a new borehole or a repair?"
    if "moving" in svc_low or "mover" in svc_low:
        return "Sure — where are you moving from and to?"
    if location_present:
        return "Thanks — could you tell me a bit more about what you need?"
    return "Sure — where are you located?"


def _warm_holding_text(conv: Any) -> str:
    """When we DO dispatch, keep it warm but not robotic. Called after offer_next chose a business."""
    # Keep short; this is after we have service+location and have found a candidate
    return "Thanks — I'm finding someone for you. I'll update you shortly."


def _conversation_turns(conv: Any) -> list[Any]:
    try:
        return list(getattr(conv, "turns", []) or [])
    except Exception:
        return []


def _last_assistant_within(conv: Any, seconds: int = 90) -> bool:
    try:
        turns = _conversation_turns(conv)
        if not turns:
            return False
        for t in reversed(turns):
            if getattr(t, "role", "") == "assistant":
                ts = getattr(t, "timestamp", None) or getattr(t, "creation", None)
                if ts is None:
                    return True  # be conservative — treat as recent
                import datetime as _dt
                now = _dt.datetime.now(UTC)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                if (now - ts).total_seconds() < seconds:
                    return True
                break
        return False
    except Exception:
        return False


def _recent_duplicate_assistant(conv: Any, text: str, seconds: int = 300) -> bool:
    """Return True if same assistant text was sent in last `seconds`."""
    try:
        turns = _conversation_turns(conv)
        for t in reversed(turns):
            if getattr(t, "role", "") == "assistant" and str(getattr(t, "message", "")).strip() == text.strip():
                ts = getattr(t, "timestamp", None) or getattr(t, "creation", None)
                if ts is None:
                    return True
                import datetime as _dt
                now = _dt.datetime.now(UTC)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                if (now - ts).total_seconds() < seconds:
                    return True
                break
        return False
    except Exception:
        return False


def is_greeting_response_text(text: str | None) -> bool:
    """True when `text` is the canonical greeting we send (used by burst guard)."""
    t = (text or "").strip().lower()
    return ("how can i help you today" in t) or ("what can i help you with" in t) or ("of course. what can i help" in t)

def _greeting_key(text: str | None) -> str | None:
    """Bucket for greeting/casual dedupe: hi vs reset vs casual. Different buckets must not suppress."""
    t = (text or "").strip().lower()
    if "of course" in t:
        return "reset"
    if "tell me what you need" in t:
        return "casual"
    if "how can i help you today" in t:
        return "hi"
    return None

_CUSTOMER_RESET_REPLY = "Of course. What can I help you with?"


def _send_assistant_turn_and_whatsapp(conv: Any, text: str) -> bool:
    """Append assistant turn then send via central. Dedup by content + narrow burst guard. Returns sent bool."""
    try:
        import frappe  # type: ignore
        try:
            doc = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": getattr(conv, "network_conversation_id", "")})
        except Exception:
            doc = conv
        # 1) Exact same text within 300s -> suppress
        if _recent_duplicate_assistant(doc, text, 300):
            return False
        # 2) Burst guard: suppress only rapid re-send of the SAME greeting bucket
        # (e.g. hi→hi or reset→reset within 10s as Meta retry). Different buckets (casual→reset)
        # or non-greeting messages must not be swallowed.
        if _last_assistant_within(doc, 10) and is_greeting_response_text(text):
            try:
                turns = _conversation_turns(doc)
                for t0 in reversed(turns):
                    if getattr(t0, "role", "") == "assistant":
                        last = str(getattr(t0, "message", "") or "")
                        if is_greeting_response_text(last):
                            # Same bucket? hi after hi is duplicate; casual after hi is different
                            if _greeting_key(text) == _greeting_key(last):
                                return False
                            # Different buckets → allow through (casual followed by reset)
                            break
                        break
            except Exception:
                return False
        from heshly_core.services.network.network_conversation_service import append_turn
        try:
            append_turn(doc, "assistant", text)
        except Exception:
            pass
        try:
            phone = getattr(doc, "customer_phone", "") or getattr(conv, "customer_phone", "")
            if phone:
                _send_whatsapp_via_central(str(phone).strip(), text)
        except Exception:
            pass
        return True
    except Exception:
        return False


def notify_customer_greeting(conversation: Any, reset: bool = False) -> None:
    """New entry-point greeting. `reset=True` when customer explicitly asked to start over."""
    text = _CUSTOMER_RESET_REPLY if reset else "Hi! How can I help you today?"
    _send_assistant_turn_and_whatsapp(conversation, text)


def notify_customer_casual(conversation: Any) -> None:
    """Neutral response for casual/general messages — no stale service injection."""
    text = "Hi! How can I help you today? Tell me what you need and where you are."
    _send_assistant_turn_and_whatsapp(conversation, text)


def notify_customer_pending(conversation: Any, raw_user_text: str | None = None) -> None:
    """Fallback for pending qualification — natural receptionist greeting. Layer 2 only."""
    try:
        import frappe  # type: ignore
        phone = getattr(conversation, "customer_phone", "")
        settings = get_network_settings()
        if not phone or not settings.central_phone_number_id:
            return
        # Decide greeting vs generic fallback
        txt = raw_user_text if raw_user_text is not None else ""
        # Fresh qualification context: if last user message was the pending one, txt is more accurate
        if not txt:
            try:
                turns = _conversation_turns(conversation)
                for t in reversed(turns):
                    if getattr(t, "role", "") == "user":
                        txt = str(getattr(t, "message", "") or "")
                        break
            except Exception:
                txt = ""
        low = (txt or "").strip().lower()
        # Priority: specific intent like "how much?" should be handled before generic greeting
        if low in ("how much?", "how much", "price?", "bei?", "cost?", "price", "how much is it?", "how much is it"):
            text = "Sure — what service are you asking about? For example: plumbing, vet, or dental?"
        elif _should_greet(txt, conversation):
            text = "Hi! 😊 How can I help you today?"
        else:
            # Generic but warm — don't sound like "finding best option"
            fallback = (getattr(settings, "fallback_message", "") or "").strip()
            # If settings fallback is robotic finding-best-option, override with human version for pending
            if fallback and "finding the best" not in fallback.lower() and "best available option" not in fallback.lower():
                text = fallback
            else:
                # Short, warm, asks what they need and where — but not heavily robotic
                text = "Hi! How can I help? Just tell me what you need and where you are — e.g. 'plumber in Nairobi'."
        _send_assistant_turn_and_whatsapp(conversation, text)
    except Exception:
        pass


def _hold_follow_up_text(conversation: Any, raw_user_text: str | None = None) -> str:
    """Human follow-up after background dispatch — contextual one-liner, not system status."""
    svc = getattr(conversation, "requested_service", "") or ""
    loc = getattr(conversation, "location", "") or ""
    txt = raw_user_text or ""
    fu = _follow_up_for_service(svc, txt, bool(loc.strip()))
    if fu:
        return fu
    return _warm_holding_text(conversation)


def notify_customer_holding(conversation: Any, raw_user_text: str | None = None) -> None:
    """Human receptionist response — short, warm, contextual. Matching happens quietly in background."""
    try:
        text = _hold_follow_up_text(conversation, raw_user_text or "")
        _send_assistant_turn_and_whatsapp(conversation, text)
    except Exception:
        pass


def notify_customer_assigned(conversation: Any) -> None:
    try:
        import frappe  # type: ignore
        try:
            doc = frappe.get_doc("Heshly Network Conversation", {"network_conversation_id": getattr(conversation, "network_conversation_id", "")})
        except Exception:
            doc = conversation
        tenant_id = getattr(doc, "assigned_tenant_id", "") or ""
        biz_name = tenant_id
        try:
            b = frappe.db.get_value("Business Account", {"tenant_id": tenant_id}, ["business_name"], as_dict=True)
            if b and b.get("business_name"):
                biz_name = b["business_name"]
        except Exception:
            pass
        text = f"You're all set — I've connected you with {biz_name}. They'll reach out shortly. If you need anything else, just let me know."
        _send_assistant_turn_and_whatsapp(doc, text)
    except Exception:
        pass
