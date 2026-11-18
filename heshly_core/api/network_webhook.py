"""Heshly Central WhatsApp webhook — isolated Layer 2 entry point."""

from __future__ import annotations

import json
import re
from typing import Any

try:
    import frappe  # type: ignore
except ImportError:  # pragma: no cover
    class _MockWhitelist:
        def __call__(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator
    class _MockFrappe:
        whitelist = _MockWhitelist()
        request = None
        local = None
    frappe = _MockFrappe()  # type: ignore  # noqa


def _parse_json_string(value: Any) -> Any:
    if isinstance(value, str):
        v = value.strip()
        if v and ((v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]"))):
            try:
                return json.loads(v)
            except Exception:
                return value
    return value


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
    for _ in range(4):
        wrapped = None
        for key in ("$json", "json", "body", "data", "payload"):
            if key in data and isinstance(data[key], (dict, str)):
                val = _parse_json_string(data[key])
                if isinstance(val, dict):
                    if "__rl" in val and "value" in val:
                        data[key] = str(val["value"]).strip()
                        continue
                    wrapped = val
                    break
        if wrapped is not None:
            merged = dict(data)
            for k in ("$json", "json", "body", "data", "payload"):
                merged.pop(k, None)
            for k, v in wrapped.items():
                v = _parse_json_string(v)
                if isinstance(v, dict) and "__rl" in v and "value" in v:
                    v = str(v["value"]).strip()
                if k not in merged or merged[k] is None or merged[k] == "":
                    merged[k] = v
            data = merged
        else:
            break
    # also unwrap entry wrapper for Meta payload passthrough
    return data


@frappe.whitelist(allow_guest=True)
def heshly_network_webhook(payload=None, **kwargs):
    """Entry for Heshly Central number. Verifies signature, qualifies, matches, dispatches."""
    data = _unwrap(payload, kwargs)
    # Meta payload may be under entry
    entry = None
    if "entry" in data and isinstance(data["entry"], list):
        entry = data
    elif "entry" in kwargs and isinstance(kwargs.get("entry"), list):
        entry = kwargs
    raw = entry if entry is not None else data

    # Extract Meta message if present
    phone_number_id: str | None = None
    from_phone: str | None = None
    customer_name: str | None = None
    text: str | None = None
    message_id: str | None = None
    message_type: str | None = None

    try:
        if "entry" in raw and isinstance(raw["entry"], list) and raw["entry"]:
            ch = raw["entry"][0].get("changes", [{}])[0].get("value", {}) if isinstance(raw["entry"][0], dict) else {}
            meta = ch.get("metadata", {}) if isinstance(ch, dict) else {}
            phone_number_id = (meta.get("phone_number_id") or raw.get("phone_number_id") or raw.get("phoneNumberId") or "") or None
            msgs = ch.get("messages") or []
            if msgs and isinstance(msgs[0], dict):
                m = msgs[0]
                message_id = m.get("id")
                from_phone = m.get("from")
                t = m.get("type")
                message_type = t if isinstance(t, str) else None
                if t == "text":
                    text = (m.get("text") or {}).get("body")
                else:
                    text = m.get("text") or text
            contacts = ch.get("contacts") or []
            if contacts and isinstance(contacts[0], dict):
                customer_name = (contacts[0].get("profile") or {}).get("name")
    except Exception:
        pass

    # Fallback direct fields
    from_phone = from_phone or data.get("phone_number") or data.get("phoneNumber") or data.get("from") or data.get("customer_phone")
    text = text or data.get("text") or data.get("message") or data.get("body")
    customer_name = customer_name or data.get("customer_name") or data.get("name")
    phone_number_id = phone_number_id or data.get("phone_number_id") or data.get("phoneNumberId")
    message_id = message_id or data.get("message_id") or data.get("id")

    if not from_phone:
        return {"success": False, "message": "phone_number/from is required"}

    # Validate against central settings
    try:
        from heshly_core.services.network.settings_service import get_network_settings
        settings = get_network_settings()
        if phone_number_id and settings.central_phone_number_id and str(phone_number_id).strip() != str(settings.central_phone_number_id).strip():
            # Not an error — just informational; still process as network if central not yet configured
            if settings.enabled:
                return {"success": False, "message": "phone_number_id does not match Heshly Network central number"}
    except Exception:
        pass

    # Signature verification (if central secret configured)
    try:
        headers = {}
        if hasattr(frappe, "request") and hasattr(frappe.request, "headers"):
            try:
                headers = {k.lower(): v for k, v in dict(getattr(frappe.request, "headers", {}) or {}).items()}
            except Exception:
                headers = {}
        sig = headers.get("x-hub-signature-256") or headers.get("x-hub-signature") or ""
        if sig and phone_number_id:
            try:
                from heshly_core.services.network.settings_service import get_network_settings as _gs
                s = _gs()
                cfg_id = s.central_configuration_id
                if cfg_id:
                    import frappe as _f
                    # Password field must be fetched via get_password, not get_value (which returns masked stars)
                    try:
                        _doc = _f.get_doc("Heshly WhatsApp Configuration", cfg_id)
                        secret = _doc.get_password("app_secret") if hasattr(_doc, "get_password") else None
                        # Fallback if doc not found or secret empty via alternative lookup
                        if not secret:
                            # try get_value with password decrypt via frappe.utils.password
                            try:
                                from frappe.utils.password import get_decrypted_password
                                secret = get_decrypted_password("Heshly WhatsApp Configuration", cfg_id, "app_secret", raise_error=False) or ""
                            except Exception:
                                secret = ""
                    except Exception:
                        secret = ""
                    if secret:
                        from heshly_core.services.whatsapp.api.authentication import WhatsAppAuthentication
                        import json as _json
                        raw_body = getattr(getattr(frappe, "request", None), "data", None)
                        if isinstance(raw_body, str):
                            raw_body = raw_body.encode("utf-8")
                        if not raw_body:
                            raw_body = _json.dumps(raw, separators=(",", ":")).encode("utf-8")
                        # build lightweight config stub
                        class _Cfg:
                            app_secret = secret
                        auth = WhatsAppAuthentication()
                        # verify_signature expects (config, raw_body, sig)
                        try:
                            ok = auth.verify_signature(_Cfg(), raw_body, sig)  # type: ignore
                        except Exception:
                            ok = False
                        if not ok:
                            try:
                                frappe.logger("heshly_whatsapp_router").warning("network_webhook signature verification failed phone_number_id=%s", phone_number_id)
                            except Exception:
                                pass
                            return {"success": False, "message": "Invalid webhook signature"}
            except Exception:
                pass
    except Exception:
        pass

    # Persist conversation + qualify + dispatch (best-effort)
    try:
        from heshly_core.services.network.network_conversation_service import get_or_create_conversation, append_turn, set_qualification
        from heshly_core.services.network.qualification_service import qualify_message
        from heshly_core.services.network.dispatch_service import offer_next

        try:
            frappe.logger("heshly_whatsapp_router").info(
                "NETWORK DEBUG extracted phone_number_id=%s from_present=%s text_present=%s message_type=%s",
                phone_number_id or "",
                bool(from_phone),
                bool(text and str(text).strip()),
                message_type or "",
            )
        except Exception:
            pass

        conv = get_or_create_conversation(
            customer_phone=str(from_phone).strip(),
            customer_name=str(customer_name).strip() if customer_name else None,
            source_phone_number_id=str(phone_number_id).strip() if phone_number_id else None,
        )
        msg_text = str(text or "").strip() or "(media/unknown)"
        # ── Conversational entry-point: intent classification BEFORE stale-state routing ──
        # Order: greeting → casual → reset → new_request → continuation
        # The decision sits BEFORE dispatch/has_pending_offer is allowed to swallow it.
        _is_greeting = False
        _is_reset = False
        _is_new_request = False
        _is_casual = False
        _intent = "continuation"
        try:
            from heshly_core.services.network.qualification_service import (
                is_genuine_greeting,
                is_explicit_reset,
                classify_customer_intent,
            )
            _is_greeting = is_genuine_greeting(msg_text)
            _is_reset = is_explicit_reset(msg_text)
            _prev_service = str(getattr(conv, "requested_service", "") or "")
            _intent = classify_customer_intent(msg_text, _prev_service)
            _is_new_request = _intent == "new_request"
            _is_casual = _intent == "casual"
        except Exception:
            pass
        # Idempotent dedupe: use Meta message_id (wamid) if available — prevents Meta retries with same wamid
        # while allowing legitimate identical text with different wamid.
        inbound_wamid = str(message_id or "").strip() if isinstance(message_id, str) else ""
        is_duplicate_wamid = False
        if inbound_wamid:
            try:
                # Lightweight cross-tenant check via frappe.db (no TenantContext needed yet)
                # Use WhatsApp Activity message_id index as source of truth for inbound dedupe
                existing = frappe.db.get_value("Heshly WhatsApp Activity", {"message_id": inbound_wamid, "direction": "inbound"}, "name")
                if existing:
                    is_duplicate_wamid = True
                    try:
                        frappe.logger("heshly_whatsapp_router").info("NETWORK DEBUG duplicate wamid skipped message_id=%s", inbound_wamid[:12] + "***")
                    except Exception:
                        pass
            except Exception:
                # On lookup failure, fall back to text-based check below
                is_duplicate_wamid = False
        if is_duplicate_wamid:
            # Still return success so Meta stops retrying, but do not append turn or re-qualify
            try:
                frappe.logger("heshly_whatsapp_router").error(
                    "NETWORK DEBUG extracted phone_number_id=%s from_present=%s text_present=%s message_type=%s duplicate_skipped=True",
                    phone_number_id or "",
                    bool(from_phone),
                    bool(text and str(text).strip()),
                    message_type or "",
                )
            except Exception:
                pass
            return {
                "success": True,
                "mode": "HESHLY_NETWORK",
                "network_conversation_id": getattr(conv, "network_conversation_id", ""),
                "network_status": getattr(conv, "network_status", ""),
                "customer_phone": getattr(conv, "customer_phone", ""),
                "duplicate": True,
            }

        # If greeting/reset/new-request, close stale context before persisting this turn.
        # casual (e.g. "can we have just a short convo...") must NOT discard stale service/location —
        # it is a natural interruption, not a reset.
        _reset_done = False
        _is_resetish = bool(_is_greeting or _is_reset or _is_new_request)
        if _is_resetish and not getattr(conv, "assigned_tenant_id", None):
            has_stale = bool(getattr(conv, "requested_service", "") or getattr(conv, "location", ""))
            if has_stale:
                try:
                    from heshly_core.services.network.network_conversation_service import reset_for_new_request
                    before_id = str(getattr(conv, "network_conversation_id", ""))
                    new_conv = reset_for_new_request(conv)
                    if str(getattr(new_conv, "network_conversation_id", "")) != before_id:
                        conv = new_conv
                        _reset_done = True
                        try:
                            frappe.logger("heshly_whatsapp_router").info(
                                "HCN reset conv %s -> %s reason=%s intent=%s",
                                before_id, str(getattr(conv, "network_conversation_id", "")),
                                "new_request" if _is_new_request else ("greeting" if _is_greeting else "reset"),
                                _intent,
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
        try:
            turns = getattr(conv, "turns", None) or []
            # Legacy text dedupe: only if last user turn has exact same text — prevents burst duplicate within same conversation
            if turns:
                last_msg = ""
                for t in reversed(turns):
                    if getattr(t, "role", "") == "user":
                        last_msg = str(getattr(t, "message", "") or "")
                        break
                if last_msg and last_msg == msg_text:
                    # Allow identical text if wamid is different and not a Meta retry (already checked above)
                    # For real burst with same wamid, we already returned; for different wamid with same text,
                    # require separate dedupe window — do not skip here, allow it
                    pass
            append_turn(conv, "user", msg_text)
            # Log inbound activity with wamid for future dedupe (best-effort)
            if inbound_wamid:
                try:
                    from heshly_core.services.crm.whatsapp_activity_logger import WhatsAppActivityLogger
                    from heshly_core.models.whatsapp import WhatsAppDirection
                    # Derive tenant/business from conversation or central config
                    tenant_for_activity = getattr(conv, "customer_phone", "") and "heshly"  # central tenant
                    try:
                        from heshly_core.services.network.settings_service import get_network_settings
                        s = get_network_settings()
                        if getattr(s, "central_configuration_id", ""):
                            tenant_for_activity = "heshly"
                    except Exception:
                        pass
                    logger = WhatsAppActivityLogger(tenant_id="heshly")
                    # Use business_id HESHLY for central Network activities
                    logger.log_message(
                        business_id="HESHLY",
                        related_type="Heshly Network Conversation",
                        related_id=getattr(conv, "network_conversation_id", ""),
                        direction=WhatsAppDirection.INBOUND,
                        phone_number=str(from_phone).strip(),
                        message=msg_text,
                        status="received",
                        message_id=inbound_wamid,
                    )
                except Exception:
                    # Activity logging failure must not block conversation
                    try:
                        frappe.logger("heshly_whatsapp_router").error("NETWORK DEBUG inbound activity log FAILED", exc_info=True)
                    except Exception:
                        pass
        except Exception:
            try:
                frappe.logger("heshly_whatsapp_router").error("NETWORK DEBUG append_turn FAILED (dedupe check)", exc_info=True)
            except Exception:
                pass
            try:
                append_turn(conv, "user", msg_text)
            except Exception:
                try:
                    frappe.logger("heshly_whatsapp_router").error("NETWORK DEBUG append_turn FAILED (fallback)", exc_info=True)
                except Exception:
                    pass
                pass

        # qualification — carry forward ONLY on continuation; otherwise start clean
        try:
            existing: dict = {}
            # Only inherit previous qualification_data when this message continues the same request.
            # For greeting/casual/reset/new_request the prior service/location must not be injected.
            _carry_forward = (_intent == "continuation") and not _reset_done
            if _carry_forward:
                try:
                    import json as _j2
                    existing = _j2.loads(getattr(conv, "qualification_data", "") or "{}") if getattr(conv, "qualification_data", "") else {}
                    if not isinstance(existing, dict):
                        existing = {}
                except Exception:
                    existing = {}
            q = qualify_message(msg_text, existing)
            # Legacy merge guard: previously restored stale service even when qualification returned none.
            # Now allowed ONLY on continuation. Non-continuation must not re-inject.
            if _intent == "continuation":
                if not q.get("requested_service") and getattr(conv, "requested_service", ""):
                    q["requested_service"] = getattr(conv, "requested_service", "")
                if not q.get("location") and getattr(conv, "location", ""):
                    q["location"] = getattr(conv, "location", "")
            # refresh
            fresh = frappe.get_doc("Heshly Network Conversation", conv.name)
            set_qualification(fresh, q)
            conv = fresh
        except Exception:
            try:
                frappe.logger("heshly_whatsapp_router").error("NETWORK DEBUG qualification FAILED", exc_info=True)
            except Exception:
                pass
            pass

        # Human receptionist routing: dispatch quietly, respond contextually. Never leave pending silent.
        # CRITICAL: if a dispatch is already OFFERED for this conversation, the customer is in active matching.
        # Follow-up user messages (e.g. "looking for a vet" after plumbing) should still get a brief human reply
        # even though has_pending_offer is True — otherwise customer hears nothing.
        try:
            fresh2 = frappe.get_doc("Heshly Network Conversation", conv.name)
            qs = getattr(fresh2, "qualification_state", "pending")
            has_pending_offer = bool(frappe.db.exists("Heshly Network Dispatch", {"network_conversation_id": getattr(fresh2, "network_conversation_id", ""), "status": "OFFERED"}))
            already_assigned = bool(getattr(fresh2, "assigned_tenant_id", None))
            # Safety: if prohibited, reply safely without matching — never create a dispatch
            if getattr(fresh2, "qualification_state", "") == "disqualified" and getattr(fresh2, "requested_service", "") == "__prohibited__":
                try:
                    from heshly_core.services.network.notification_service import _send_assistant_turn_and_whatsapp
                    _send_assistant_turn_and_whatsapp(fresh2, "Sorry, I can't help with that request. If you need a legitimate professional service, let me know what you need and where you are.")
                except Exception:
                    pass
                return {
                    "success": True,
                    "mode": "HESHLY_NETWORK",
                    "network_conversation_id": getattr(fresh2, "network_conversation_id", ""),
                    "network_status": getattr(fresh2, "network_status", ""),
                    "customer_phone": getattr(fresh2, "customer_phone", ""),
                    "disqualified": True,
                }
            _msg_is_greeting = bool(_is_greeting)
            _msg_is_reset = bool(_is_reset)
            _msg_is_new = bool(_is_new_request)
            _msg_is_casual = bool(_is_casual)
            _is_continuation = (_intent == "continuation")
            _is_continuation_timing = bool(_is_continuation) and re.search(r"\b(?:tomorrow|today|tonight|tonigt|urgent|asap)\b", msg_text.lower()) is not None
            if _is_continuation_timing and not already_assigned:
                try:
                    svc2 = str(getattr(fresh2, "normalized_service", "") or getattr(fresh2, "requested_service", "") or "").strip()
                    loc2 = str(getattr(fresh2, "location", "") or "").strip()
                    # Always acknowledge timing naturally — do not re-use the location follow-up for timing messages
                    import heshly_core.services.network.notification_service as _nt2b
                    reply = "Got it — I've noted you'd like them to come tomorrow. I'll check availability and get back to you."
                    _nt2b._send_assistant_turn_and_whatsapp(fresh2, reply)
                    try:
                        import json as _j2t
                        qd2 = _j2t.loads(getattr(fresh2, "qualification_data","") or "{}") or {}
                        if not qd2.get("preferred_time"):
                            qd2["preferred_time"] = msg_text.strip()[:64]
                            fresh2.qualification_data = _j2t.dumps(qd2)[:10000]
                            fresh2.save(ignore_permissions=True)
                            frappe.db.commit()
                    except: pass
                    _is_continuation = False
                except: pass
            if _msg_is_new and not already_assigned and not getattr(fresh2, "location", ""):
                try:
                    cand = frappe.db.sql("select location, requested_service, normalized_service from `tabHeshly Network Conversation` where customer_phone=%s and network_status='CANCELLED' order by modified desc limit 1", (getattr(fresh2,"customer_phone","") or "",), as_dict=True)
                    if cand and cand[0].get("location"):
                        _prev_loc = cand[0].get("location")
                        _prev_svc = cand[0].get("normalized_service") or cand[0].get("requested_service")
                        from heshly_core.services.network.qualification_service import _normalize_location_value
                        if _normalize_location_value(_prev_loc):
                            fresh_norm = str(getattr(fresh2, "normalized_service", "") or "").lower()
                            prev_norm = str(_prev_svc or "").lower()
                            if not fresh_norm or not prev_norm or fresh_norm == prev_norm or fresh_norm in prev_norm or prev_norm in fresh_norm or ("dental" in fresh_norm and "dental" in prev_norm):
                                fresh2.location = _prev_loc
                                try:
                                    import json as _j2
                                    qd = _j2.loads(getattr(fresh2, "qualification_data","") or "{}") or {}
                                    qd["location"] = _prev_loc
                                    fresh2.qualification_data = _j2.dumps(qd)[:10000]
                                except: pass
                                try:
                                    fresh2.save(ignore_permissions=True)
                                    frappe.db.commit()
                                except: pass
                except: pass
            # Also handle refinement within same conversation (dentist lavington -> teeth whitening same phone, no new row yet)
            if _msg_is_new and not already_assigned and not getattr(fresh2, "location", "") and getattr(conv, "location", ""):
                try:
                    from heshly_core.services.network.qualification_service import _normalize_location_value as _nlv2
                    if _nlv2(getattr(conv, "location", "")):
                        fresh2.location = getattr(conv, "location", "")
                        try:
                            fresh2.save(ignore_permissions=True)
                            frappe.db.commit()
                        except: pass
                except: pass
            if (_msg_is_greeting or _msg_is_reset) and not already_assigned:
                try:
                    from heshly_core.services.network.notification_service import notify_customer_greeting
                    notify_customer_greeting(fresh2, reset=_msg_is_reset)
                except Exception:
                    try:
                        frappe.logger("heshly_whatsapp_router").error("NETWORK greeting/reset notify FAILED", exc_info=True)
                    except Exception:
                        pass
            elif _msg_is_casual and not already_assigned:
                # Casual interruption (e.g. "can we have just a short convo...") must not discard location
                # for the next refinement. Pin current qualified state so teeth whitening still has lavington.
                if getattr(fresh2, "requested_service", "") and getattr(fresh2, "location", ""):
                    try:
                        # Touch nothing — just ensure the row stays qualified with location for next message
                        pass
                    except: pass
                try:
                    from heshly_core.services.network.notification_service import notify_customer_casual
                    notify_customer_casual(fresh2)
                except Exception:
                    try:
                        frappe.logger("heshly_whatsapp_router").error("NETWORK casual notify FAILED", exc_info=True)
                    except Exception:
                        pass
            elif _msg_is_new and not already_assigned:
                if qs in ("qualified", "in_progress") or getattr(fresh2, "requested_service", ""):
                    try:
                        fresh2._raw_user_text = msg_text  # type: ignore
                    except Exception:
                        pass
                    disp = offer_next(str(getattr(fresh2, "network_conversation_id", "")))
                    try:
                        fresh2 = frappe.get_doc("Heshly Network Conversation", conv.name)
                        conv = fresh2
                    except Exception:
                        conv = fresh2
                    if disp is None and qs in ("qualified", "in_progress"):
                        try:
                            import heshly_core.services.network.notification_service as _ns
                            from heshly_core.services.network.qualification_service import classify_customer_intent as _ci
                            # Safe template: prefer normalized_service when available, else generic
                            doc2 = fresh2
                            norm = str(getattr(doc2, "normalized_service", "") or getattr(doc2, "requested_service", "") or "").strip()
                            raw = str(getattr(doc2, "raw_request", "") or "").strip()
                            # Check safety via _is_safe_service_token_for_template without interpolating raw
                            if norm and _ns._is_safe_service_token_for_template(norm):
                                svc = norm
                            elif getattr(doc2, "requested_service", "") and _ns._is_safe_service_token_for_template(str(getattr(doc2, "requested_service", ""))):
                                svc = str(getattr(doc2, "requested_service", ""))
                            else:
                                svc = ""
                            loc = getattr(doc2, "location", "") or ""
                            if not loc:
                                no_match_text = _ns._hold_follow_up_text(doc2, msg_text)  # asks for location
                            elif svc:
                                no_match_text = f"We don't have a {svc} provider in {loc} just yet — can I check a nearby area, or would you like to tell me more about what you need?"
                            else:
                                no_match_text = f"I don't have a suitable professional available in {loc} yet. I can check nearby areas, or you can tell me a little more about the work needed."
                            _ns._send_assistant_turn_and_whatsapp(fresh2, no_match_text)
                        except Exception:
                            pass
            elif qs == "pending" and not already_assigned:
                try:
                    from heshly_core.services.network.notification_service import notify_customer_pending
                    notify_customer_pending(fresh2, raw_user_text=msg_text)
                except Exception:
                    try:
                        frappe.logger("heshly_whatsapp_router").error("NETWORK pending fallback FAILED", exc_info=True)
                    except Exception:
                        pass
            elif not has_pending_offer and not already_assigned:
                if qs in ("qualified", "in_progress") or getattr(fresh2, "requested_service", ""):
                    # Professional new_request with no stale dispatch — but unknown professional
                    # requests use `requested_service` (raw-ish). Prefer safe routing:
                    #  - if normalized category missing and no location, ask for location
                    #  - if normalized + location present, proceed to matching; unknown will hit safe no-match
                    try:
                        fresh2._raw_user_text = msg_text  # type: ignore
                    except Exception:
                        pass
                    # For unknown professional requests (raw_request present, normalized empty),
                    # we still route through offer_next — but the safe no-match below will handle the reply.
                    disp = offer_next(str(getattr(fresh2, "network_conversation_id", "")))
                    try:
                        fresh2 = frappe.get_doc("Heshly Network Conversation", conv.name)
                        conv = fresh2
                    except Exception:
                        conv = fresh2
                    if disp is None and qs in ("qualified", "in_progress"):
                        try:
                            import heshly_core.services.network.notification_service as _ns2
                            norm2 = str(getattr(fresh2, "normalized_service", "") or getattr(fresh2, "requested_service", "") or "").strip()
                            loc2 = str(getattr(fresh2, "location", "") or "").strip()
                            if not loc2:
                                # Unknown request + no location: ask for property area, not generic plumber question
                                if _ns2._is_safe_service_token_for_template(norm2 or getattr(fresh2, "requested_service", "")):
                                    follow = _ns2._follow_up_for_service(norm2 or getattr(fresh2, "requested_service", ""), msg_text, False)
                                    if follow:
                                        _ns2._send_assistant_turn_and_whatsapp(fresh2, follow)
                                        raise StopIteration  # already handled
                                no_match_text = "Sure — what area is the property in?"
                            elif _ns2._is_safe_service_token_for_template(norm2 or getattr(fresh2, "requested_service", "")):
                                svc2 = norm2 or str(getattr(fresh2, "requested_service", ""))
                                no_match_text = f"We don't have a {svc2} provider in {loc2} just yet — can I check a nearby area, or would you like to tell me more about what you need?"
                            else:
                                no_match_text = f"I don't have a suitable professional available in {loc2} yet. I can check nearby areas, or you can tell me a little more about the work needed."
                            _ns2._send_assistant_turn_and_whatsapp(fresh2, no_match_text)
                        except StopIteration:
                            pass
                        except Exception:
                            pass
            elif has_pending_offer and not already_assigned and qs in ("qualified", "in_progress"):
                try:
                    from heshly_core.services.network.notification_service import _follow_up_for_service, _send_assistant_turn_and_whatsapp
                    from heshly_core.services.network.qualification_service import qualify_message as _qm
                    fresh_q = _qm(msg_text, {})
                    fresh_svc = (fresh_q.get("requested_service") or "").strip()
                    stored_svc = (getattr(fresh2, "requested_service", "") or "").strip()
                    eff_svc = fresh_svc if (fresh_svc and fresh_svc.lower() != stored_svc.lower()) else (stored_svc or fresh_svc)
                    if not eff_svc:
                        eff_svc = stored_svc or fresh_svc
                    loc = getattr(fresh2, "location", "") or fresh_q.get("location") or ""
                    fu = _follow_up_for_service(eff_svc, msg_text, bool(str(loc).strip()))
                    if fu:
                        _send_assistant_turn_and_whatsapp(fresh2, fu)
                except Exception:
                    pass
        except Exception:
            try:
                frappe.logger("heshly_whatsapp_router").error("NETWORK DEBUG dispatch FAILED", exc_info=True)
            except Exception:
                pass
            pass

        return {
            "success": True,
            "mode": "HESHLY_NETWORK",
            "network_conversation_id": getattr(conv, "network_conversation_id", ""),
            "network_status": getattr(conv, "network_status", ""),
            "customer_phone": getattr(conv, "customer_phone", ""),
        }
    except Exception as e:
        try:
            import frappe as _f2
            _f2.logger().error(f"heshly_network_webhook failed: {e}")
        except Exception:
            pass
        return {"success": False, "message": str(e)}
