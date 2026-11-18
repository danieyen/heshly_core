from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta, date, time
import json
import re

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.models.conversation import (
    Conversation,
    ConversationStatus,
    ConversationTurn,
    ExtractedEntities,
    Speaker,
)
from heshly_core.models.intent import Intent
from heshly_core.repositories.conversation_repository import ConversationRepository
from heshly_core.services.ai.tenant_ai_manager import TenantAIManager
from heshly_core.services.ai.intent_classifier import IntentClassifier
from heshly_core.services.ai.entity_extractor import EntityExtractor
from heshly_core.services.ai.completeness_checker import CompletenessChecker
from heshly_core.services.ai.business_rules import BusinessRules
from heshly_core.services.ai.action_planner import ActionPlanner
from heshly_core.services.qualification.qualification_engine import QualificationEngine
from heshly_core.models.qualification import QualificationStatus


# ============================================================
# Helpers
# ============================================================

def _tenant() -> str:
    return TenantContext().require()


def _require_business():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    business_id = frappe.session.data.get("heshly_business_id")
    if not business_id:
        frappe.throw("Business session not found.", frappe.PermissionError)
    business = frappe.db.get_value(
        "Business Account",
        {"business_id": business_id, "status": "Active"},
        ["business_id", "business_name", "tenant_id", "industry", "timezone", "currency"],
        as_dict=True,
    )
    if not business:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    membership = frappe.db.get_value(
        "User Business Membership",
        {"user": frappe.session.user, "business_id": business.business_id, "tenant_id": business.tenant_id, "active": 1},
        "name",
    )
    if not membership:
        frappe.throw("You do not have access to this business.", frappe.PermissionError)
    return business


def _get_ai_config(tenant_id: str):
    name = frappe.db.get_value("AI Configuration", {"tenant_id": tenant_id}, "name")
    if name:
        doc = frappe.get_doc("AI Configuration", name)
        return {
            "ai_enabled": bool(doc.ai_enabled),
            "personality": doc.personality,
            "qualification_enabled": bool(doc.qualification_enabled),
            "automatic_booking_enabled": bool(doc.automatic_booking_enabled),
            "human_escalation_enabled": bool(doc.human_escalation_enabled),
        }
    return {
        "ai_enabled": True,
        "personality": "Friendly & professional",
        "qualification_enabled": True,
        "automatic_booking_enabled": True,
        "human_escalation_enabled": True,
    }


def _normalize_date(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip().lower()
    today = date.today()
    if s == "today":
        return today.isoformat()
    if s == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    m = re.match(r"next\s+(\w+)", s)
    if m:
        weekday_name = m.group(1).lower()
        weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
        if weekday_name in weekdays:
            target = weekdays[weekday_name]
            days_ahead = (target - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).isoformat()
    # try ISO already
    try:
        # if contains T, split
        if "T" in s:
            s = s.split("T")[0]
        d = date.fromisoformat(s)
        return d.isoformat()
    except Exception:
        pass
    return raw.strip()


def _normalize_time(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip().lower()
    # handle "2 pm" or "2:30 pm" or "14:00"
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", s)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        mer = m.group(3)
        if mer == "pm" and hour < 12:
            hour += 12
        if mer == "am" and hour == 12:
            hour = 0
        if hour > 23 or minute > 59:
            return None
        return f"{hour:02d}:{minute:02d}"
    # already HH:MM
    try:
        if ":" in s:
            parts = s.split(":")
            h = int(parts[0])
            mi = int(parts[1].split(" ")[0])
            return f"{h:02d}:{mi:02d}"
    except Exception:
        pass
    return raw.strip()


def _merge_entities(old: ExtractedEntities, new: ExtractedEntities) -> ExtractedEntities:
    return ExtractedEntities(
        service=(new.service or old.service),
        date=(new.date or old.date),
        time=(new.time or old.time),
        customer_name=(new.customer_name or old.customer_name),
        phone=(new.phone or old.phone),
        email=(new.email or old.email),
        extras={**(old.extras or {}), **(new.extras or {})},
    )


def _evaluate_rules_with_knowledge(intent_val, entities: ExtractedEntities, knowledge) -> tuple[bool, str | None]:
    br = BusinessRules()
    if intent_val == Intent.BOOK_APPOINTMENT:
        # HESHLY canonical tenant's BusinessKnowledgeProfile is polluted with feature descriptions
        # (e.g. "AI Receptionist"), not bookable services — never enforce that as an allowlist.
        tenant_services = (knowledge.services or []) if knowledge else []
        # Only enforce knowledge allowlist if there is at least one plausible *booking* service name.
        # Heuristic: short (<=30 chars) and looks like a care/service offering, not a platform feature.
        booking_keywords = ("cleaning", "consultation", "checkup", "whitening", "filling", "implant", "treatment", "therapy", "massage", "consult")
        plausible = []
        for s in tenant_services:
            t = s.strip()
            if not t or len(t) > 30:
                continue
            low = t.lower()
            # Exclude platform feature names even if short (e.g. "AI Receptionist", "Appointment Booking")
            if low in ("ai receptionist", "appointment booking", "availability checking", "customer qualification", "lead and customer management"):
                continue
            if any(k in low for k in booking_keywords) or low in ("dental cleaning", "consultation", "checkup", "whitening", "filling"):
                plausible.append(t)
        # If we have plausible booking services, enforce; otherwise delegate to BusinessRules (which knows Dental Cleaning etc.)
        if plausible:
            allowed_set = {s.lower() for s in plausible}
            if entities.service:
                req = entities.service.strip().lower()
                if req not in allowed_set:
                    matched = any(req in svc or svc in req for svc in allowed_set)
                    if not matched:
                        return False, f"Service '{entities.service}' is not offered. Available: {', '.join(plausible[:6])}"
                return True, None
            return True, None
        return (br.evaluate(intent_val, entities).allowed, br.evaluate(intent_val, entities).reason)
    res = br.evaluate(intent_val, entities)
    return res.allowed, res.reason


def _build_ai_message(
    intent_result,
    entities: ExtractedEntities,
    completeness,
    rules_allowed, rules_reason,
    action_plan,
    qualification_result, qualification_action, qualification_response,
    knowledge,
    availability_result: dict | None,
    handover: bool,
    booking_result: dict | None,
    mode: str,
) -> str:
    intent = intent_result.intent if intent_result else Intent.UNKNOWN

    # Handover takes precedence
    if handover:
        if intent == Intent.HUMAN_SUPPORT:
            return "Of course — I'll connect you with our team. A human colleague will take over this conversation shortly."
        if rules_allowed is False:
            return f"Thanks for your message. {rules_reason or 'That request is outside what I can handle automatically.'} Let me bring in our team to help you directly."
        if qualification_result and qualification_result.status == QualificationStatus.ESCALATED:
            return "Thanks for sharing those details — I'll escalate this to our team so they can review your eligibility and get back to you."
        return "I'm handing this conversation to our human team. They'll have the full context and will follow up shortly."

    # FAQ-like intents answered from knowledge
    if intent in (Intent.BUSINESS_HOURS, Intent.LOCATION, Intent.PRICE_INQUIRY, Intent.SERVICE_INQUIRY):
        if knowledge:
            if intent == Intent.BUSINESS_HOURS:
                # try to find hours in policies/faqs
                for faq in knowledge.faqs or []:
                    if "hour" in faq.lower() or "open" in faq.lower():
                        # faq may be "question|answer"
                        if "|" in faq:
                            return faq.split("|", 1)[1].strip()
                        return faq
                return f"{knowledge.business_name or 'We'} are typically open Monday to Saturday. Let me check availability for a specific time if you'd like to book."
            if intent == Intent.PRICE_INQUIRY:
                # search services/policies for price
                if entities.service:
                    for svc in knowledge.services or []:
                        if entities.service.lower() in svc.lower():
                            return f"For {entities.service}, our standard offering is listed under services. A colleague can share an exact quote if needed — would you like me to check a time?"
                return "Pricing depends on the specific service. Tell me which treatment you're interested in and I can check options and availability."
            if intent == Intent.LOCATION:
                return f"{knowledge.business_name or 'We'} serve clients primarily in {knowledge.industry or 'our area'}. Share your location and I'll confirm."
            if intent == Intent.SERVICE_INQUIRY:
                if knowledge.services:
                    return f"We offer: {', '.join(knowledge.services[:6])}. Which one would you like help with?"
                if knowledge.description:
                    return knowledge.description[:300]
        # fallback
        if intent == Intent.BUSINESS_HOURS:
            return "We're open Monday to Saturday — tell me your preferred date and time and I'll check availability."
        if intent == Intent.PRICE_INQUIRY:
            return "Pricing depends on the service. Which service are you asking about?"
        return knowledge.description[:300] if knowledge and knowledge.description else "Happy to help — what would you like to know?"

    # Booking completeness
    if completeness and not completeness.complete:
        missing = completeness.missing_fields or []
        if "service" in missing:
            if knowledge and knowledge.services:
                return f"Which service would you like to book? We offer: {', '.join(knowledge.services[:6])}."
            return "Which service would you like to book?"
        if "date" in missing:
            return "What date works for you? (e.g., tomorrow or next Tuesday)"
        if "time" in missing:
            return "What time would you prefer? (e.g., 2pm or 10:00)"

    # Rules blocked
    if rules_allowed is False:
        return f"{rules_reason or 'That request cannot be completed automatically.'} I'll bring in our team."

    # Qualification asks
    if qualification_response:
        # flow already provides a question
        return qualification_response

    # Availability outcomes
    if action_plan and action_plan.action.value == "create_appointment":
        if availability_result is not None:
            if availability_result.get("available") is False:
                reason = availability_result.get("reason") or "That slot is not available."
                if "No active calendar" in reason or "calendar connection" in reason.lower():
                    return f"I've checked availability — {reason} A team member will confirm the time and complete the booking."
                return f"That time isn't available — {reason} Would you like to try another time?"
            if availability_result.get("available") is True:
                if mode == "live" and booking_result:
                    if booking_result.get("success"):
                        start = booking_result.get("appointment", {}).get("start") or booking_result.get("appointment_id")
                        return f"Your appointment is confirmed — {entities.service or 'Appointment'} on {entities.date or ''} at {entities.time or ''}. Reference {booking_result.get('appointment_id')}."
                    else:
                        err = booking_result.get("error") or "Booking failed."
                        return f"I found the slot available, but the booking could not be completed — {err} Our team will follow up to secure it."
                else:
                    return f"Good news — that slot looks available for {entities.service or 'your appointment'} on {entities.date or ''} at {entities.time or ''}. In live mode this would be booked directly; in dry-run I don't create the calendar event."
        return "All required information is collected. I can check availability when you're ready."

    if action_plan:
        return action_plan.reason or "Thanks for your message — how can I help further?"

    return "Thanks for your message. How can I help you today?"


def _build_timeline(intent_result, entities: ExtractedEntities, qualification_result, completeness, rules_allowed, availability_result, booking_result, handover: bool, mode: str):
    now = datetime.now(UTC)
    def ts(i):
        return (now + timedelta(seconds=i)).isoformat()
    tl = []
    tl.append({"at": ts(0), "label": "Customer message received"})
    if intent_result:
        tl.append({"at": ts(1), "label": f"Intent detected: {intent_result.intent.value} ({int((intent_result.confidence or 0)*100)}%)"})
    if entities.service or entities.date or entities.time:
        tl.append({"at": ts(2), "label": f"Entities — service: {entities.service or '—'}, date: {entities.date or '—'}, time: {entities.time or '—'}"})
    if qualification_result:
        tl.append({"at": ts(3), "label": f"Qualification: {qualification_result.status.value} (score {qualification_result.score:.1f}, urgency {qualification_result.urgency.value})"})
        if qualification_result.missing_fields:
            tl.append({"at": ts(3), "label": f"Qualification needs: {', '.join(qualification_result.missing_fields)}"})
    if completeness:
        if completeness.complete:
            tl.append({"at": ts(4), "label": "Booking information complete"})
        else:
            tl.append({"at": ts(4), "label": f"Booking needs: {', '.join(completeness.missing_fields)}"})
    tl.append({"at": ts(5), "label": f"Business rules: {'allowed' if rules_allowed else 'blocked'}"})
    if availability_result is not None:
        tl.append({"at": ts(6), "label": f"Availability: {'available' if availability_result.get('available') else 'unavailable'} — {availability_result.get('reason','')[:120]}"})
        if availability_result.get("available") is False and availability_result.get("reason"):
            tl.append({"at": ts(6), "label": "Failure reported — no false success"})
    if booking_result is not None:
        if booking_result.get("success"):
            tl.append({"at": ts(7), "label": f"Appointment booked — {booking_result.get('appointment_id')}"})
        elif booking_result.get("dry_run"):
            tl.append({"at": ts(7), "label": "Dry-run — would book, no calendar event created"})
        else:
            tl.append({"at": ts(7), "label": f"Booking failed — {booking_result.get('error','unknown')[:120]}"})
    if handover:
        tl.append({"at": ts(8), "label": "Escalated to human"})
    else:
        tl.append({"at": ts(8), "label": "Handled by AI"})
    return tl


def _build_outcome(entities: ExtractedEntities, qualification_result, booking_result, handover: bool, intent_result):
    qual_label = "—"
    if qualification_result:
        s = qualification_result.status.value
        if s == "qualified":
            qual_label = "HOT" if qualification_result.score >= 0.7 else "WARM"
        elif s == "not_qualified":
            qual_label = "NOT QUALIFIED"
        elif s == "collecting_info":
            qual_label = "COLLECTING"
        elif s == "escalated":
            qual_label = "ESCALATED"
        else:
            qual_label = s.upper()
    appt = None
    if booking_result and booking_result.get("success"):
        appt = booking_result.get("appointment", {})
        appt_str = appt.get("start") or booking_result.get("appointment_id")
        appt = appt_str
    elif booking_result and booking_result.get("dry_run"):
        appt = f"Would book {entities.date or '?'} {entities.time or ''}".strip()
    return {
        "customer": entities.customer_name or "Simulated Customer",
        "service": entities.service or "—",
        "date": entities.date or "—",
        "time": entities.time or "—",
        "phone": entities.phone or "—",
        "qualification": qual_label,
        "qualification_score": getattr(qualification_result, "score", None),
        "urgency": getattr(qualification_result, "urgency", None).value if qualification_result and hasattr(qualification_result.urgency, "value") else None,
        "appointment": appt,
        "appointment_raw": booking_result,
        "handover": handover,
        "status": "Ready for human follow-up" if handover else ("Appointment confirmed" if booking_result and booking_result.get("success") else "AI handled"),
        "intent": intent_result.intent.value if intent_result else None,
    }


def _load_or_create_conversation(conversation_id: str | None, tenant_id: str) -> Conversation:
    repo = ConversationRepository()
    if conversation_id:
        conv = repo.get(conversation_id, tenant_id=tenant_id)
        if conv is not None:
            return conv
        conv = Conversation(conversation_id=conversation_id, customer_id=f"sim_{tenant_id}", status=ConversationStatus.ACTIVE)
        return conv
    new_id = f"sim_{tenant_id}_{uuid.uuid4().hex[:10]}"
    return Conversation(conversation_id=new_id, customer_id=f"sim_{tenant_id}", status=ConversationStatus.ACTIVE)


# ============================================================
# Whitelisted API
# ============================================================

@frappe.whitelist()
def simulate(message: str = "", conversation_id: str = "", mode: str = "dry_run", customer_name: str = "", phone: str = ""):
    """
    Multi-turn simulator turn.

    - same TenantContext, same BusinessKnowledgeProfile, same AI Configuration,
      same qualification/availability/booking/handover engines.
    - channel = "simulator" (WhatsApp is "whatsapp")
    - Preserves conversation state between messages.
    - Dry-run runs availability without creating calendar event.
    - Live runs AvailabilityAPI then BookingAPI with real provider.
    """
    tenant_id = _tenant()
    business = _require_business()
    ai_cfg = _get_ai_config(tenant_id)
    if not ai_cfg.get("ai_enabled"):
        frappe.throw("AI Receptionist is paused for this business.")

    message = (message or "").strip()
    if not message:
        frappe.throw("Message is required.")
    mode = (mode or "dry_run").strip().lower()
    if mode not in ("dry_run", "live"):
        mode = "dry_run"
    conversation_id = (conversation_id or "").strip() or None
    customer_name = (customer_name or "").strip()
    phone = (phone or "").strip()

    # Load knowledge
    manager = TenantAIManager()
    knowledge = manager.knowledge(tenant_id)

    # Load or create conversation
    conv = _load_or_create_conversation(conversation_id, tenant_id)
    # If caller supplied customer_name/phone, seed entities
    if customer_name and not conv.entities.customer_name:
        conv.entities.customer_name = customer_name
    if phone and not conv.entities.phone:
        conv.entities.phone = phone
    # Also allow phone/customer_name overrides per-turn
    if customer_name:
        conv.entities.customer_name = customer_name
    if phone:
        conv.entities.phone = phone

    # --- AI pipeline with history merge ---
    classifier = IntentClassifier()
    extractor = EntityExtractor()
    checker = CompletenessChecker()
    planner = ActionPlanner()
    qual_engine = QualificationEngine()

    intent_result = classifier.classify(message)
    new_entities = extractor.extract(message)
    # Enrich customer_name/phone from explicit params
    if customer_name:
        new_entities.customer_name = customer_name
    if phone:
        new_entities.phone = phone
    # Merge with history
    merged = _merge_entities(conv.entities, new_entities)
    # Normalize date/time to ISO where possible for downstream engines
    if merged.date:
        norm_d = _normalize_date(merged.date)
        if norm_d:
            merged.date = norm_d
    if merged.time:
        norm_t = _normalize_time(merged.time)
        if norm_t:
            merged.time = norm_t

    # Qualification (collect data from merged)
    collected = {
        "customer_name": merged.customer_name,
        "phone": merged.phone,
        "email": merged.email,
        "service": merged.service,
        "date": merged.date,
        "time": merged.time,
    }
    required = ["customer_name", "phone"]
    # If AI config disables qualification, skip requiring those? Keep but mark qualified
    if not ai_cfg.get("qualification_enabled"):
        required = []
    qual_result, qual_action, qual_response = qual_engine.qualify(
        customer_id=conv.customer_id, message=message, collected_data=collected, required_fields=required
    )

    # Completeness and rules
    completeness = checker.check(intent_result.intent, merged)
    rules_allowed, rules_reason = _evaluate_rules_with_knowledge(intent_result.intent, merged, knowledge)
    # BusinessRules evaluation alone (for planner) — create a RuleResult-like bool
    from heshly_core.models.workflow import RuleResult
    rules = RuleResult(allowed=rules_allowed, reason=rules_reason)
    action = planner.plan(intent_result.intent, completeness, rules if completeness.complete else None)

    # Human handoff determination
    handover = False
    handover_reason = None
    if intent_result.intent == Intent.HUMAN_SUPPORT:
        handover = True
        handover_reason = "Customer requested human support"
    elif action.action.value == "escalate_human":
        handover = True
        handover_reason = rules_reason or action.reason
    elif qual_action and qual_action.value == "escalate":
        handover = True
        handover_reason = "Qualification escalated"
    elif not ai_cfg.get("human_escalation_enabled") is False and False:
        pass
    # Respect ai config human escalation toggle: if disabled, don't auto-handover except explicit HUMAN_SUPPORT
    if not ai_cfg.get("human_escalation_enabled") and handover and intent_result.intent != Intent.HUMAN_SUPPORT:
        # keep but allow AI to handle
        pass

    # Availability (dry-run always when booking intent and complete)
    availability_result = None
    if intent_result.intent == Intent.BOOK_APPOINTMENT and completeness.complete and rules_allowed:
        try:
            from heshly_core.api.availability import AvailabilityAPI
            api = AvailabilityAPI()
            payload = {
                "service": merged.service,
                "preferred_date": merged.date,
                "preferred_time": merged.time,
                "tenant_id": tenant_id,
            }
            availability_result = api.check(payload)
            # ensure booleans
            if not isinstance(availability_result, dict):
                availability_result = {"available": False, "slots": [], "reason": "Invalid availability response"}
        except Exception as e:
            availability_result = {"available": False, "slots": [], "reason": f"Availability check failed: {str(e)[:300]}"}

    # Booking (only if available and not handover)
    booking_result = None
    if availability_result and availability_result.get("available") and not handover:
        if mode == "live" and ai_cfg.get("automatic_booking_enabled"):
            try:
                from heshly_core.api.booking import BookingAPI
                bapi = BookingAPI()
                b_payload = {
                    "tenant_id": tenant_id,
                    "service": merged.service,
                    "date": merged.date,
                    "time": merged.time,
                    "customer_name": merged.customer_name or "Simulated Customer",
                    "phone_number": merged.phone or "sim",
                    "customer_id": conv.customer_id,
                }
                booking_result = bapi.book_appointment(b_payload)
                if not isinstance(booking_result, dict):
                    booking_result = {"success": False, "error": "Invalid booking response"}
            except Exception as e:
                booking_result = {"success": False, "error": f"Booking failed: {str(e)[:300]}"}
        else:
            # dry-run — do NOT create event
            booking_result = {"success": False, "dry_run": True, "would_book": True, "service": merged.service, "date": merged.date, "time": merged.time, "message": "Dry-run: slot available, no calendar event created"}

    # Build AI message
    ai_message = _build_ai_message(
        intent_result, merged, completeness, rules_allowed, rules_reason, action,
        qual_result, qual_action, qual_response, knowledge, availability_result, handover, booking_result, mode
    )

    # Persist turns (user + assistant)
    now = datetime.now(UTC)
    conv.add_turn(ConversationTurn(role=Speaker.USER, message=message, timestamp=now))
    conv.add_turn(ConversationTurn(role=Speaker.ASSISTANT if not handover else Speaker.SYSTEM, message=ai_message, timestamp=now + timedelta(milliseconds=200)))
    # Update entities and status
    conv.entities = merged
    if handover:
        conv.status = ConversationStatus.HANDOVER
    elif booking_result and booking_result.get("success"):
        conv.status = ConversationStatus.COMPLETED
    else:
        conv.status = ConversationStatus.ACTIVE

    repo = ConversationRepository()
    # Doctype channel enum is whatsapp/web/sms/phone/other — simulator uses "web" (maps to simulator display)
    repo.save(conv, tenant_id=tenant_id, channel="web", intent=intent_result.intent.value)

    # Persist qualification to Lead (update existing, no duplicates) — reuse qualification engine as source of truth
    try:
        from heshly_core.services.crm.lead_persistence import persist_qualification_to_lead
        persist_qualification_to_lead(
            tenant_id=tenant_id,
            customer_name=merged.customer_name,
            phone=merged.phone,
            email=merged.email,
            qual_result=qual_result,
        )
    except Exception as _e:
        # Do not break simulator on Lead persistence failure
        try:
            frappe.logger().warning(f"simulate: persist_qualification_to_lead failed: {_e}")
        except Exception:
            pass

    # Build crm preview
    crm_preview = {
        "customer_name": merged.customer_name or "Simulated Customer",
        "phone": merged.phone or "—",
        "email": merged.email or "—",
        "service": merged.service or "—",
        "date": merged.date or "—",
        "time": merged.time or "—",
        "qualification_status": qual_result.status.value if qual_result else None,
        "qualification_score": getattr(qual_result, "score", None),
        "urgency": getattr(qual_result, "urgency", None).value if qual_result and hasattr(qual_result.urgency, "value") else None,
        "would_create_lead": handover or (qual_result.status.value == "qualified" if qual_result else False),
    }

    timeline = _build_timeline(intent_result, merged, qual_result, completeness, rules_allowed, availability_result, booking_result, handover, mode)
    outcome = _build_outcome(merged, qual_result, booking_result, handover, intent_result)

    # Human brief for escalated
    human_brief = None
    if handover:
        try:
            from heshly_core.services.handover.handover_engine import HumanHandoverEngine
            engine = HumanHandoverEngine()
            res = engine.process(
                customer_id=conv.customer_id,
                conversation_id=conv.conversation_id,
                department="support",
                customer_name=merged.customer_name,
                customer_phone=merged.phone,
                requested_service=merged.service,
                qualification_status=qual_result.status.value if qual_result else None,
                urgency=qual_result.urgency.value if qual_result and hasattr(qual_result.urgency, "value") else "low",
                escalation_reason=handover_reason or rules_reason or "Simulator escalation",
                messages=[t.message for t in conv.turns[-6:]],
                customer_requested_human=(intent_result.intent == Intent.HUMAN_SUPPORT),
                ai_confidence=float(intent_result.confidence or 0.9),
            )
            if res and isinstance(res, dict) and "request" in res:
                req = res["request"]
                human_brief = {
                    "priority": getattr(getattr(req, "priority", ""), "value", str(getattr(req, "priority", ""))),
                    "reason": getattr(getattr(req, "reason", ""), "value", str(getattr(req, "reason", ""))),
                    "queue": getattr(getattr(req, "queue", ""), "value", str(getattr(req, "queue", ""))) if hasattr(req, "queue") else None,
                }
        except Exception as e:
            human_brief = {"error": str(e)[:300]}

    # Serialize turns
    turns_out = [
        {"role": t.role.value if hasattr(t.role, "value") else str(t.role), "message": t.message, "timestamp": t.timestamp.isoformat() if hasattr(t.timestamp, "isoformat") else str(t.timestamp)}
        for t in conv.turns
    ]

    return {
        "conversation_id": conv.conversation_id,
        "customer_id": conv.customer_id,
        "status": conv.status.value if hasattr(conv.status, "value") else str(conv.status),
        "channel": "simulator",
        "tenant_id": tenant_id,
        "mode": mode,
        "turns": turns_out,
        "entities": merged.to_dict(),
        "intent": {"value": intent_result.intent.value, "confidence": float(intent_result.confidence), "reasoning": intent_result.reasoning},
        "completeness": {"complete": completeness.complete, "missing_fields": completeness.missing_fields},
        "rules": {"allowed": bool(rules_allowed), "reason": rules_reason},
        "action": {"value": action.action.value, "reason": action.reason},
        "qualification": {
            "status": qual_result.status.value if qual_result else None,
            "score": getattr(qual_result, "score", None),
            "urgency": getattr(qual_result, "urgency", None).value if qual_result and hasattr(qual_result.urgency, "value") else None,
            "missing_fields": getattr(qual_result, "missing_fields", []),
            "eligible": getattr(qual_result, "eligible", None),
            "action": qual_action.value if qual_action and hasattr(qual_action, "value") else str(qual_action) if qual_action else None,
            "response": qual_response,
        },
        "availability": availability_result,
        "booking": booking_result,
        "ai_message": ai_message,
        "handover": handover,
        "handover_reason": handover_reason,
        "human_brief": human_brief,
        "timeline": timeline,
        "outcome": outcome,
        "crm_preview": crm_preview,
        "knowledge": {
            "business_name": knowledge.business_name if knowledge else business.business_name,
            "industry": knowledge.industry if knowledge else business.industry,
            "services": knowledge.services if knowledge else [],
        },
    }


@frappe.whitelist()
def get_simulation(conversation_id: str):
    tenant_id = _tenant()
    _require_business()
    if not conversation_id:
        frappe.throw("conversation_id is required")
    repo = ConversationRepository()
    conv = repo.get(conversation_id.strip(), tenant_id=tenant_id)
    if not conv:
        frappe.throw("Conversation not found", frappe.DoesNotExistError)
    return {
        "conversation_id": conv.conversation_id,
        "customer_id": conv.customer_id,
        "status": conv.status.value if hasattr(conv.status, "value") else str(conv.status),
        "entities": conv.entities.to_dict(),
        "turns": [
            {"role": t.role.value if hasattr(t.role, "value") else str(t.role), "message": t.message, "timestamp": t.timestamp.isoformat() if hasattr(t.timestamp, "isoformat") else str(t.timestamp)}
            for t in conv.turns
        ],
        "turn_count": len(conv.turns),
    }


@frappe.whitelist()
def reset_simulation():
    tenant_id = _tenant()
    _require_business()
    new_id = f"sim_{tenant_id}_{uuid.uuid4().hex[:10]}"
    return {"conversation_id": new_id}
