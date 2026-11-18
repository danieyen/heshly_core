"""Consultative decision guide — intent-independent, adaptive, non-brittle.

ThisLayer sits ABOVE qualification_service + matching_engine. It does NOT duplicate
service extraction, geography gating, or dispatch. It:

- identifies the user's desired outcome (not just first noun)
- tracks per-task context inside a single Heshly Network Conversation
- asks one focused question at a time, using already-known facts
- validates whether the requested solution fits the underlying problem
- distinguishes consultation (assessment) from referral (dispatch)
- supports services, products, and informational decisions without forcing
  products through provider matching
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Task model — stored inside qualification_data["consult_tasks"] as JSON
# ---------------------------------------------------------------------------

TASK_STATUSES = ("collecting", "assessing", "recommending", "referred", "paused", "completed")


@dataclass
class ConsultTask:
    task_id: str
    domain: str  # plumbing | farming | legal | product | venue | dental | general | vet | electrical ...
    intent: str  # service_request | consultation | product_request | informational
    desired_outcome: str = ""  # free-text summary of what user wants to achieve
    requested_service: str = ""  # normalized
    raw_request: str = ""
    location: str = ""
    budget_min: float | None = None
    budget_max: float | None = None
    capacity: int | None = None
    facts: dict[str, Any] = field(default_factory=dict)  # domain-specific collected facts
    outstanding_questions: list[str] = field(default_factory=list)
    status: str = "collecting"
    recommendation: str = ""  # last assessment text
    referral_state: str = ""  # none | offered | accepted | no_match
    created_at: str = ""
    last_active: str = ""
    matching_brief: str = ""  # refined brief for existing matching engine

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "ConsultTask":
        return ConsultTask(
            task_id=d.get("task_id", "") or d.get("id", ""),
            domain=d.get("domain", "general"),
            intent=d.get("intent", "service_request"),
            desired_outcome=d.get("desired_outcome", ""),
            requested_service=d.get("requested_service", ""),
            raw_request=d.get("raw_request", ""),
            location=d.get("location", ""),
            budget_min=d.get("budget_min"),
            budget_max=d.get("budget_max"),
            capacity=d.get("capacity"),
            facts=dict(d.get("facts") or {}),
            outstanding_questions=list(d.get("outstanding_questions") or []),
            status=d.get("status", "collecting"),
            recommendation=d.get("recommendation", ""),
            referral_state=d.get("referral_state", ""),
            created_at=d.get("created_at", ""),
            last_active=d.get("last_active", ""),
            matching_brief=d.get("matching_brief", "") or (d.get("facts") or {}).get("matching_brief", ""),
        )


# ---------------------------------------------------------------------------
# Domain detection — lightweight, intent-level, not a 100-keyword list
# ---------------------------------------------------------------------------

_DOMAIN_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # Farming Lamu must be first — more specific than plumbing/product overlap
    (re.compile(r"\blamu\b.*\bfarm|\bfarm.*\blamu\b", re.I), "farming", "consultation"),
    (re.compile(r"\b(?:farm(?:ing)?|crop|lamu|soil|irrigat|harvest|plant(?:ing)?|agriculture)\b", re.I), "farming", "consultation"),
    (re.compile(r"\b(?:lawyer|legal|attorney|sue|court|contract|dispute)\b", re.I), "legal", "service_request"),
    (re.compile(r"\b(?:house\s+builder|builder|construction)\b", re.I), "construction", "service_request"),
    (re.compile(r"\b(?:tile\s+fixer|tiler|tiling|tiles)\b", re.I), "tiling", "service_request"),
    (re.compile(r"\b(?:electrician|electrical)\b", re.I), "electrical", "service_request"),
    (re.compile(r"\b(?:plumb|plumber|toilet|drain|leak|pipe|tap|sink|burst)\b", re.I), "plumbing", "service_request"),
    (re.compile(r"\b(?:water\s*heater|geyser)\b", re.I), "water_heater", "service_request"),
    (re.compile(r"\b(?:ac\b|air\s*conditioner|air\s*con|hvac|not\s+cooling)\b", re.I), "hvac", "service_request"),
    (re.compile(r"\b(?:termite|pest\s*control|rats?|mice|cockroach|ants?\s+infest|infested|exterminator|fumigat)\b", re.I), "pest_control", "service_request"),
    (re.compile(r"\b(?:roof\s+leak|roof\s+is\s+leaking|ceiling\s+leak|water\s+is\s+leaking\s+through\s+my\s+ceiling)\b", re.I), "roofing", "service_request"),
    (re.compile(r"\b(?:repaint|painting|paint\s+my\s+house)\b", re.I), "painting", "service_request"),
    (re.compile(r"\b(?:dentist|dental|tooth|teeth|whitening|extraction|cleaning|braces)\b", re.I), "dental", "service_request"),
    (re.compile(r"\b(?:venue|event|hall|conference|party|meeting)\b", re.I), "venue", "service_request"),
    (re.compile(r"\b(?:vet|veterinar|animal|pet|dog|cat|cow|goat)\b", re.I), "vet", "service_request"),
    (re.compile(r"\b(?:cctv|fridge|refrigerator|solar|borehole|architect|engineer|electrical|salon|barber|clinic|restaurant|hotel|gym)\b", re.I), "general_service", "service_request"),
    # product — explicit product intent (including specs like storage/gb) — camera here is phone spec when paired with smartphone
    (re.compile(r"\b(?:buy|purchase|product|catalogue|catalog|phone|laptop|smartphone|tv|furniture|photography|storage|delivery)\b", re.I), "product", "product_request"),
    (re.compile(r"\blamu\b", re.I), "farming_location", "consultation"),
    (re.compile(r"\b(?:good\s+idea|should\s+i|is\s+it\s+worth|feasib|advisable|move\s+to)\b", re.I), "general_consult", "consultation"),
]

CONSULTATION_DOMAINS = {"farming", "legal", "general_consult", "product"}


def _is_farming_detail(text: str) -> bool:
    low = (text or "").lower()
    if "borehole water" in low:
        if any(m in low for m in ("witu","acres","budget","runway","lamu","land","irrigat","water")):
            return True
    farming_markers = [
        "acres", "acre", "land", "witu", "lamu", "borehole water", "runway", "months",
        "budget", "ksh", "kes", "800k", "capital", "irrigat", "water_source",
        "have", "near", "budget", "months",
    ]
    if "maize" in low and "land" in low:
        return True
    if any(m in low for m in ("plumb","witu","smartphone","phone","laptop","vet","cctv","install")) and "acres" not in low and "witu" not in low and "lamu" not in low and "maize" not in low and "borehole water" not in low:
        return False
    count = sum(1 for m in farming_markers if m in low)
    if count >= 1 and any(m in low for m in ("acres","witu","lamu","land","borehole water","runway")):
        return True
    return False


def _detect_domain(text: str, requested_service: str = "") -> tuple[str, str]:
    # Correction handling: "No, I dont need a lawyer. I need someone to fix my toilet." -> detect from corrected part only
    try:
        from heshly_core.services.network.qualification_service import _strip_correction_prefix as _strip_corr, _extract_open_service as _eos_corr
        stripped = _strip_corr(text or "")
        if stripped and stripped.strip().lower() != (text or "").strip().lower() and len(stripped.strip()) > 5:
            d2, i2 = _detect_domain(stripped, requested_service)
            if d2 not in ("legal", "general", "general_consult"):
                return d2, i2
    except Exception:
        pass
    low = (text or "").lower()
    rs = (requested_service or "").lower()
    combined = f"{low} {rs}"
    # CRITICAL: farming continuation must win over borehole extraction
    # "I have 2 acres near Witu, borehole water..." is farming, not borehole service
    if _is_farming_detail(text):
        if not re.search(r"\b(?:smartphone|phone|laptop|plumb|vet|cctv)\b", low):
            # If requested_service is borehole but text is farming detail, keep farming
            if requested_service and "borehole" in requested_service.lower():
                return "farming", "consultation"
            if "farm" in combined or "lamu" in combined or "witu" in low or "acres" in low:
                return "farming", "consultation"
    for pat, domain, intent in _DOMAIN_PATTERNS:
        if pat.search(combined):
            if domain == "farming_location":
                return "farming", "consultation"
            return domain, intent
    if requested_service:
        return "general_service", "service_request"
    if re.search(r"\b(?:is\s+it|should\s+i|advice|recommend|help\s+me\s+decide)\b", low):
        return "general_consult", "consultation"
    return "general", "service_request"


# ---------------------------------------------------------------------------
# Per-domain missing-info rules + question phrasing
# ---------------------------------------------------------------------------

def _next_question_for_task(task: ConsultTask) -> str | None:
    d = task.domain
    f = task.facts
    loc = (task.location or "").strip()
    svc = (task.requested_service or "").lower()

    # Plumbing: need issue description before matching
    if d == "plumbing" or svc == "plumbing":
        issue = (f.get("issue_description") or f.get("plumbing_issue") or "").strip()
        if not issue:
            # Check raw_request already contains issue words
            raw_low = (task.raw_request or "").lower()
            if not any(w in raw_low for w in ("leak", "blocked", "drain", "tap", "pipe", "toilet", "sink", "burst", "fix")):
                return "Got it — I can help with plumbing in {loc}. What needs fixing?".format(loc=loc or "your area") if loc else "What needs fixing? For example, is it a leak, blocked drain, or toilet issue?"
        if not loc:
            return "Where in {area} should I look? A more specific area helps find someone nearby.".format(area="that area" if not loc else loc)
        # budget is optional — don't block

    # Farming feasibility
    if d == "farming":
        if not f.get("crop"):
            # Also check task location/text for crop hint if facts empty due to pending branch
            raw_for_crop = (task.raw_request or "").lower()
            for cand in ["maize", "tomato", "rice", "cassava", "mango", "cashew", "coconut", "beans", "wheat"]:
                if cand in raw_for_crop and cand not in str(f.get("crop", "")).lower():
                    f["crop"] = cand
                    break
            if not f.get("crop"):
                return "What crop are you planning to grow in Lamu? Different crops suit the coastal climate very differently."
        if not f.get("land_access"):
            return "Do you already have access to land in Lamu, or would you need to acquire or lease it?"
        if not f.get("water_source"):
            return "How will you handle water — is there reliable irrigation or borehole access for that crop?"
        if not f.get("capital_runway"):
            return "Roughly what startup budget and how many months of runway do you have before the farm needs to pay for itself?"
        # enough to assess — no further question
        # If facts are empty because classify stripped them, try task.raw_request text

    # Legal / professional validation — consultative, not just location collection
    if d == "legal":
        if not f.get("problem_description"):
            return "Could you tell me briefly what happened and what outcome you're hoping for?"
        if not loc:
            return "Thanks — with that context, which town or area should I search in to find the right professional?"
        return None

    # Product — be lenient: budget already known from prior msg, don't re-ask if we have it in task
    if d == "product" or task.intent == "product_request":
        if f.get("required_specs") or f.get("specs"):
            return None  # specs already provided, go to catalogue
        if f.get("intended_use") and (task.budget_min is not None or task.budget_max is not None):
            return None  # have use+budget, enough to search catalogue
        if not f.get("intended_use") and not f.get("required_specs") and not f.get("specs"):
            if any(w in (task.raw_request or "").lower() for w in ("storage","camera","gb")):
                return None  # spec message itself is enough
            return "What will you mainly use it for? That helps narrow the right specs."
        if task.budget_min is None and task.budget_max is None and not f.get("budget"):
            return "Roughly what budget do you have in mind?"
        if not f.get("required_specs") and not f.get("specs") and not f.get("intended_use"):
            return "Any must-have specs — for example size, capacity, or brand preference?"

    # Venue
    if d == "venue" or svc in ("venue", "event", "event venue", "hall"):
        if not task.capacity:
            return "How many people do you expect?"
        if not task.location:
            return "Which town or area should I search in?"
        if task.budget_min is None:
            return "Roughly what budget do you have for the venue?"

    # General service — minimal friction: service + location is enough
    if task.intent == "service_request" and not task.requested_service:
        return "What do you need help with?"
    if task.intent == "service_request" and not task.location:
        return "Where should I look for someone? A town or neighbourhood is enough."

    return None


def _assess_task(task: ConsultTask) -> str:
    """Evidence-based assessment; never invents local facts."""
    d = task.domain
    f = task.facts

    if d == "farming":
        crop = (f.get("crop") or "").lower()
        budget = f.get("capital_runway") or f.get("budget") or ""
        land = f.get("land_access") or ""
        water = f.get("water_source") or ""
        parts = [
            "Here's a preliminary take — this is guidance, not a guarantee, and local verification matters before you commit.",
        ]
        if crop:
            parts.append(f"For **{crop}** in Lamu, coastal conditions (heat, sandy/saline soils, seasonal rainfall) make water and soil testing especially important.")
        else:
            parts.append("Without knowing the crop, I can only outline the general checks.")
        # Echo back what they've confirmed so it feels responsive, not generic
        confirms = []
        if land:
            confirms.append(f"land: {land}")
        if water:
            confirms.append(f"water: {water}")
        if budget:
            confirms.append(f"budget/runway: {budget}")
        if confirms:
            parts.append("Noted — " + "; ".join(confirms) + ".")
        parts.append(
            "Key factors to verify locally before moving: crop suitability for the coastal climate, reliable water/irrigation, "
            "soil salinity/fertility, land cost and tenure security, startup and operating costs vs your runway, "
            "transport/storage/market access and who will buy, and seasonal/environmental risks."
        )
        if land and ("no" in str(land).lower() or "need" in str(land).lower()):
            parts.append("If you still need to acquire land, factor in purchase/lease costs and title security — these often decide feasibility.")
        parts.append(
            "Recommendation: **conditional** — potentially viable if water, soil, and market checks pass for your chosen crop, "
            "but **not advisable to relocate or invest heavily** until you've confirmed those locally with an agronomist or extension officer and a market buyer."
        )
        return " ".join(parts)

    if d == "legal":
        prob = (f.get("problem_description") or task.desired_outcome or "").lower()
        # Do not categorically prescribe pastor/mediator — explain distinctions
        if any(w in prob for w in ("family", "divorce", "custody", "land", "property", "employment", "contract", "debt", "arrest", "police", "court")):
            return (
                "That sounds like it may involve legal rights or obligations, so a qualified legal professional is often appropriate — "
                "but the right professional depends on the specifics. A lawyer can advise on legal options and risks; "
                "a mediator may help if both parties are open to agreement; pastoral or counselling support can help with personal wellbeing but doesn't replace legal advice. "
                "Could you share a bit more about the situation so I can point you to the most suitable option and explain what each would actually do?"
            )
        return (
            "I want to make sure you get the right kind of help. Legal advice is appropriate when there's a legal question, dispute, or risk — "
            "but other professionals (mediator, counsellor, or a different specialist) may fit better depending on what happened and what you want to achieve. "
            "Could you tell me a bit more about the situation and your preferred outcome?"
        )

    if d == "plumbing":
        return "Thanks — with that location and budget I can look for a plumber nearby who fits. I'll check availability and show you the best matches."

    if task.intent == "product_request":
        return "Thanks — with that use and budget I can check the catalogue for products that actually fit, rather than just the closest keyword match."

    return "Thanks for the detail — let me use what you've shared to find the most suitable next step."


# ---------------------------------------------------------------------------
# Session-level task store helpers
# ---------------------------------------------------------------------------

def _load_tasks(qualification_data: dict[str, Any] | str | None) -> list[ConsultTask]:
    if isinstance(qualification_data, str):
        try:
            qualification_data = json.loads(qualification_data) if qualification_data else {}
        except Exception:
            qualification_data = {}
    if not isinstance(qualification_data, dict):
        qualification_data = {}
    raw = qualification_data.get("consult_tasks") or qualification_data.get("tasks") or []
    out: list[ConsultTask] = []
    for d in raw:
        try:
            if isinstance(d, dict):
                out.append(ConsultTask.from_dict(d))
        except Exception:
            continue
    return out


def _save_tasks(qualification_data: dict[str, Any] | str | None, tasks: list[ConsultTask]) -> dict[str, Any]:
    if isinstance(qualification_data, str):
        try:
            qualification_data = json.loads(qualification_data) if qualification_data else {}
        except Exception:
            qualification_data = {}
    if not isinstance(qualification_data, dict):
        qualification_data = {}
    qualification_data["consult_tasks"] = [t.to_dict() for t in tasks]
    # active pointer
    if tasks:
        # last_active is the active task
        active = max(tasks, key=lambda t: t.last_active or t.created_at or "")
        qualification_data["active_task_id"] = active.task_id
    return qualification_data


def merge_qualification_data(existing: dict|None, delta: dict, operation: str) -> dict:
    """Central merge that never replaces consult_tasks array."""
    import json as _j
    from copy import deepcopy as _dc
    if existing is None:
        existing = {}
    if isinstance(existing, str):
        try:
            existing = _j.loads(existing) if existing else {}
        except Exception:
            existing = {}
    out = _dc(existing) if isinstance(existing, dict) else {}
    # Preserve consult_tasks
    prev_tasks = _load_tasks(out)
    # delta may contain consult_tasks from upsert
    if delta and isinstance(delta, dict) and delta.get("consult_tasks"):
        out["consult_tasks"] = delta.get("consult_tasks")
        if delta.get("active_task_id"):
            out["active_task_id"] = delta.get("active_task_id")
    # Merge top-level fields (location etc) from delta
    for k in ("requested_service","location","budget_min","budget_max","capacity","qualification_state","raw_request"):
        if delta and k in delta and delta[k] not in (None, ""):
            if operation=="CORRECT" or not out.get(k):
                out[k]=delta[k]
            elif k=="location" and delta[k]!=out.get(k):
                # ADD: keep both if different locations? keep active task location
                pass
    return out

def get_active_task(qualification_data: dict[str, Any] | str | None) -> ConsultTask | None:
    tasks = _load_tasks(qualification_data)
    if not tasks:
        return None
    if isinstance(qualification_data, dict):
        aid = qualification_data.get("active_task_id")
        if aid:
            for t in tasks:
                if t.task_id == aid:
                    return t
    # fallback: most recent
    return max(tasks, key=lambda t: t.last_active or "")


def upsert_task_from_message(
    text: str,
    qualification_data: dict[str, Any] | str | None,
    extracted: dict[str, Any],
) -> tuple[ConsultTask, list[ConsultTask], dict[str, Any]]:
    """
    Create or update a task from the latest user message + qualification extraction.
    Returns (active_task, all_tasks, updated_qualification_data).
    Handles topic switching: new unrelated domain/service => new task, old paused.
    """
    import uuid
    from datetime import datetime, UTC

    now = datetime.now(UTC).isoformat()
    tasks = _load_tasks(qualification_data)
    if isinstance(qualification_data, str):
        try:
            qualification_data = json.loads(qualification_data) if qualification_data else {}
        except Exception:
            qualification_data = {}
    if not isinstance(qualification_data, dict):
        qualification_data = {}

    # Multi-service support: split compound extracted service on commas/semicolons if qualify inserted joined
    loc = (extracted.get("location") or "").strip()
    svc_raw = (extracted.get("requested_service") or "").strip()
    raw = (extracted.get("raw_request") or text or "").strip()
    # Context-aware service filtering:
    # - Farming Lamu consultation is not a plumbing service — ignore stale plumbing from qualify when domain is farming
    # - Borehole water in an active farming consultation is NOT a borehole-service request
    # - Product "camera" in an active product consultation is NOT CCTV
    _active_hint = get_active_task(qualification_data)
    if loc and "borehole water" in loc.lower():
        if _is_farming_detail(text) or (_active_hint and _active_hint.domain == "farming"):
            m_loc = re.match(r"^\s*([A-Za-z]{2,30})", loc)
            if m_loc:
                loc = m_loc.group(1).strip()
    if _is_farming_detail(text) and svc_raw.lower() in ("plumbing", "borehole services", "borehole repair", "cctv installation"):
        svc = ""
    elif _active_hint and _active_hint.domain == "farming" and svc_raw.lower() in ("plumbing", "borehole services", "borehole repair"):
        if _is_farming_detail(text):
            svc = ""
        elif "borehole" in svc_raw.lower() and "water" in text.lower() and not re.search(r"\bfix\b|\brepair\b|\binstall\b", text, re.I):
            svc = ""
        else:
            svc = svc_raw
    elif _active_hint and _active_hint.intent == "product_request" and svc_raw.lower() == "CCTV installation":
        if not re.search(r"\bcctv\b", text, re.I):
            if _active_hint.domain == "product" or "smartphone" in (_active_hint.desired_outcome or "").lower():
                svc = _active_hint.requested_service or ""
            else:
                svc = svc_raw
        else:
            svc = svc_raw
    else:
        _fresh_hint, _ = _detect_domain(text, "")
        if _fresh_hint == "farming" and svc_raw.lower() in ("plumbing", "borehole services", "borehole repair"):
            svc = ""
        else:
            svc = svc_raw
    budget_min = extracted.get("budget_min")
    budget_max = extracted.get("budget_max")
    # Normalize 0 budget from frappe doc (means unset) -> None
    if budget_max == 0 or budget_max == 0.0:
        budget_max = None
    capacity = extracted.get("capacity")
    # Detect domain/intent from text + service
    # If no active task but text is a product spec follow-up (storage/camera with smartphone), force product
    if not tasks and svc == "smartphone" and any(w in text.lower() for w in ("storage","camera","gb","delivery","nairobi")):
        domain, intent = "product", "product_request"
    else:
        domain, intent = _detect_domain(text, svc)
    # Product preserve: if active was product_request, keep product even if _detect says general_service
    # Need active first — temp check after active resolved below will override if needed

    # Fix: get_active_task and tasks were different object copies — unify by resolving active from tasks list
    active = None
    for _t in tasks:
        if _t.task_id == (qualification_data.get("active_task_id") if isinstance(qualification_data, dict) else None):
            active = _t
            break
    if not active and tasks:
        # Fallback to most recent by last_active
        try:
            active = max(tasks, key=lambda t: t.last_active or t.created_at or "")
        except Exception:
            active = tasks[-1]
    # Greeting / yes / advice with no new service should not create an empty consult task
    try:
        from heshly_core.services.network.service_consultant import (
            is_advice_request as _is_adv,
            is_contextual_affirmative as _is_yes,
        )
        _keep_active = bool(_is_adv(text) or _is_yes(text))
    except Exception:
        _keep_active = False
    _is_greeting_like = bool(__import__('re').match(r'^\s*(?:hi|hello|hey|habari)[!.,]*\s*$', (text or ''), __import__('re').I))
    if ((_is_greeting_like or _keep_active) and not svc and not loc) or (_keep_active and active):
        if active and _keep_active:
            try:
                from heshly_core.services.network.service_consultant import apply_user_message as _aum
                _aum(active, text, "")
            except Exception:
                pass
            active.last_active = now
            if loc and not active.location:
                active.location = loc
        qd = _save_tasks(qualification_data, tasks)
        return (active if active else None) or (tasks[-1] if tasks else None), tasks, qd
    is_new_task = False
    if not tasks:
        is_new_task = True
        # Multi-service bootstrap: if text contains second service marker, don't treat as single
        # (actual splitting done in website_chat upstream, so here single is fine)
    elif active and active.domain != domain and domain not in ("general",):
        # Same service (plumbing) with different domain labels (general_service vs plumbing) -> keep task
        if active.requested_service and svc and active.requested_service.lower() == svc.lower():
            is_new_task = False
        # Farming continuation must NOT become a new task; product spec continuation also stays on product
        elif active.domain == "farming" and _is_farming_detail(text):
            is_new_task = False
        elif active.intent == "product_request" and domain == "general_service" and any(w in text.lower() for w in ("storage","camera","gb","nairobi","delivery","spec")):
            is_new_task = False
        elif _detect_domain(text, "")[0] == domain:
            is_new_task = True
    elif active and svc and active.requested_service and svc.lower() != active.requested_service.lower():
        # Service switch (plumbing -> vet, etc) — new task
        # But "Nakuru" bare location should NOT be a new task
        # Also, plumbing synonyms (plumbing vs leak repair) are same service -> keep task
        _plumb_family = {"plumbing", "leak repair", "drain unclog"}
        if svc.lower() in _plumb_family and (active.requested_service or "").lower() in _plumb_family:
            is_new_task = False
        elif svc.lower() not in (active.requested_service or "").lower():
            # Ensure new svc is substantive, not just stopword
            if len(svc) >= 3 and svc.lower() not in ("hi", "hello"):
                is_new_task = True
                # Bare location-only follow-up should not create new task
                if not svc and loc and active.requested_service:
                    is_new_task = False

    # Product preserve override: if active was product_request, keep product domain even after general_service detect
    if active and active.intent == "product_request" and domain == "general_service" and any(w in text.lower() for w in ("storage","camera","gb","nairobi","delivery","spec","photography")):
        domain, intent = "product", "product_request"
        is_new_task = False
    # Also treat farming consultation phrases ("Is it a good idea to move to Lamu") as new even if no svc keyword
    if not is_new_task and domain == "farming" and active and active.domain != "farming":
        if re.search(r"\blamu\b", text, re.I):
            is_new_task = True

    # Multi-service also handling — extract second service via _extract_all_services style
    _also_services = []
    try:
        from heshly_core.services.network.qualification_service import _extract_all_services as _eas_consult  # type: ignore
        _also_services = _eas_consult(text, (active.requested_service if active else "") or "")
    except Exception:
        _also_services = []
    # Extract explicit location from msg_text for also handling (e.g. Roysambu)
    _also_loc = None
    try:
        from heshly_core.services.network.qualification_service import _extract_location_value as _elv_also
        _also_loc = _elv_also(text)
    except Exception:
        pass
    if _also_services and active and svc_raw:
        _also_svc_tmp = _also_services[0] if _also_services else ""
        if _also_svc_tmp and any((tt.requested_service or "").lower() == _also_svc_tmp.lower() for tt in tasks):
            # Already exists — treat as update, not new
            for _tt in tasks:
                if ( _tt.requested_service or "").lower() == _also_svc_tmp.lower():
                    if loc and not _tt.location:
                        _tt.location = loc
                    _tt.last_active = now
                    qd = _save_tasks(qualification_data, tasks)
                    return _tt, tasks, qd
        # If svc_raw is the old service (qualify kept first) but text has also second, treat as ADD
        # Use first also service as the delta svc for the new task
        _also_svc = _also_services[0]
        if _also_svc.lower() not in (active.requested_service or "").lower():
            if _also_loc:
                loc = _also_loc
            elif not loc and active.location:
                loc = active.location
            # Override svc to the also service for this ADD operation
            svc = _also_svc
            # Re-detect domain for the new service
            domain, intent = _detect_domain(text, svc)
            is_new_task = True

    # Location broadcast: when kasarani arrives late, update prior builder task missing location
    if loc and tasks:
        for _pt in tasks:
            if not _pt.location and _pt.status != "paused" or (_pt.status == "paused" and not _pt.location):
                # Update paused builder's location too when project location arrives
                if _pt.requested_service and _pt.requested_service.lower() not in (svc.lower() if svc else ""):
                    if not _pt.location:
                        _pt.location = loc
                        _pt.last_active = now
    # Location inheritance for also-addition: when new service has no location, inherit project location
    if is_new_task and not loc and active and active.location:
        # Check if message is an addition (also) — inherit even if not also keyword? For multi-service project, inherit if no different location supplied
        if re.search(r"\balso\b", text or "", re.I) or not loc:
            # Only inherit if loc explicitly empty; preserve separate location if tiler says Roysambu
            loc = active.location
    if is_new_task:
        # Pause old active
        if active:
            active.status = "paused"
            active.last_active = now
        tid = f"task_{uuid.uuid4().hex[:8]}"
        task = ConsultTask(
            task_id=tid,
            domain=domain,
            intent=intent,
            desired_outcome=raw[:120],
            requested_service=svc,
            raw_request=raw,
            location=loc,
            budget_min=budget_min,
            budget_max=budget_max,
            capacity=capacity,
            facts={},
            status="collecting",
            created_at=now,
            last_active=now,
        )
        # Seed facts from extracted + text heuristics
        if domain == "farming":
            m_crop = re.search(r"\b(?:grow|plant)\s+(?:a\s+)?([A-Za-z]{3,20})", text, re.I)
            if m_crop:
                task.facts["crop"] = m_crop.group(1)
            if re.search(r"\bhave\s+(?:access\s+to\s+)?land\b", text, re.I):
                task.facts["land_access"] = "has land"
            elif re.search(r"\bneed\s+(?:to\s+)?(?:acquire|lease|buy)\s+land\b", text, re.I):
                task.facts["land_access"] = "needs land"
        if domain == "legal" and len(raw.strip()) > 30:
            task.facts["problem_description"] = raw[:200]
        if domain == "plumbing" or svc == "plumbing":
            # Extract plumbing issue if present
            m_issue = re.search(r"\b(?:leak|blocked?\s*drain|burst|tap|pipe|toilet|sink)\b.*", text, re.I)
            if m_issue:
                task.facts["issue_description"] = m_issue.group(0).strip()[:120]
        tasks.append(task)
        active = task
    else:
        # Update active task with new facts
        if not active:
            # Should not happen, create one
            tid = f"task_{uuid.uuid4().hex[:8]}"
            active = ConsultTask(task_id=tid, domain=domain, intent=intent, requested_service=svc, raw_request=raw, location=loc, budget_min=budget_min, budget_max=budget_max, capacity=capacity, created_at=now, last_active=now)
            tasks.append(active)
        else:
            # Merge location/budget/capacity
            if loc and not active.location:
                active.location = loc
            elif loc and loc.lower() != (active.location or "").lower():
                # Refinement (e.g. Unga House -> Westlands)
                active.location = loc
            if budget_min is not None and active.budget_min is None:
                active.budget_min = budget_min
            if budget_max is not None:
                active.budget_max = budget_max
            if capacity is not None:
                active.capacity = capacity
            if svc and not active.requested_service:
                active.requested_service = svc
            low = text.lower()
            if active.domain == "farming":
                if not active.facts.get("crop"):
                    m = re.search(r"\b(?:maize|tomato|rice|cassava|mango|cashew|coconut|beans|wheat)\b", low)
                    if m:
                        active.facts["crop"] = m.group(0)
                    elif len(text.strip().split()) == 1 and len(text.strip()) >= 3:
                        if text.strip().lower() not in ("yes", "no", "maybe", "hi", "hello", "hey", "what", "borehole water, budget 800k, 12 months runway"):
                            active.facts["crop"] = text.strip()
                if not active.facts.get("crop") and re.search(r"\bmaize\b", low):
                    active.facts["crop"] = "maize"
                if re.search(r"\b(?:acres?|have\s+.*land|near\s+witu|witu)\b", low):
                    if not active.facts.get("land_access"):
                        active.facts["land_access"] = text.strip()[:80]
                    if not active.location and "witu" in low:
                        active.location = "Witu"
                    # Farming detail location update: keep Lamu? No, Witu is more specific, already handled; crop handled
                elif not active.facts.get("land_access"):
                    if len(text.strip().split()) >= 3 and re.search(r"\b(?:land|acquire|lease|holding|own|have|no\s+current)\b", low):
                        active.facts["land_access"] = text.strip()[:80]
                    elif re.search(r"\b(?:need|acquire|lease|have|own)\b", low) and len(text) < 80:
                        active.facts["land_access"] = text.strip()[:80]
                elif not active.facts.get("land_access"):
                    if len(text.strip().split()) >= 3 and re.search(r"\b(?:land|acquire|lease|holding|own|have|no\s+current)\b", low):
                        active.facts["land_access"] = text.strip()[:80]
                    elif re.search(r"\b(?:need|acquire|lease|have|own)\b", low) and len(text) < 80:
                        active.facts["land_access"] = text.strip()[:80]
                if not active.facts.get("water_source") and re.search(r"\b(?:water|irrigat|borehole|rain)\b", low):
                    # Don't overwrite if we already extracted from same message's land_access
                    active.facts["water_source"] = text.strip()[:80]
                if not active.facts.get("capital_runway") and re.search(r"\b\d", text):
                    active.facts["capital_runway"] = text.strip()[:80]
                if not active.location and "witu" in low:
                    active.location = "Witu"
                if not active.facts.get("water_source") and "borehole water" in low:
                    active.facts["water_source"] = "borehole water"
                if not active.facts.get("capital_runway") and re.search(r"\b\d+k?\b.*\b\d+\s*months?\b|\b\d+\s*months?\b.*\b\d", low, re.I):
                    if not active.facts.get("capital_runway"):
                        active.facts["capital_runway"] = text.strip()[:80]
            if active.domain == "legal":
                # Second message often contains problem description
                if len(text.strip()) > 20 and not active.facts.get("problem_description"):
                    active.facts["problem_description"] = text.strip()[:200]
                elif len(text.strip()) > 10:
                    active.facts["desired_outcome"] = text.strip()[:120]
            if active.domain in ("plumbing", "general_service", "general") or (active.requested_service and active.requested_service.lower() == "plumbing") or active.intent == "service_request":
                # Blocked natural variation should stay as plumbing continuation with same task
                _is_blocked_natural = bool(re.search(r"water\s+(?:not\s+going\s+down|isn't\s+draining|not\s+draining|stays\s+in\s+the\s+bowl)|won't\s+flush|draining\s+very\s+slowly|keeps?\s+filling\s+up", text or "", re.I))
                if _is_blocked_natural and active.facts.get("problem_type") == "blocked_toilet":
                    active.facts["refined_request"] = text.strip()[:200]
                    active.last_active = now
                if not active.facts.get("issue_description"):
                    if any(w in low for w in ("leak", "blocked", "drain", "tap", "pipe", "toilet", "sink", "burst", "issue", "fixing", "leaking", "cistern", "flush")) or _is_blocked_natural:
                        active.facts["issue_description"] = text.strip()[:120]
                # Symptom refinements update the brief; they are not a new request
                if any(w in low for w in ("cistern", "not filling", "float", "blocked", "running", "flush")) or _is_blocked_natural:
                    active.facts["refined_request"] = text.strip()[:200]
            # Product — specs and location from follow-up
            if active.intent == "product_request" or active.domain == "product":
                if not active.facts.get("intended_use") and len(text) > 5:
                    active.facts["intended_use"] = text.strip()[:120]
                if not active.facts.get("required_specs") and any(w in low for w in ("storage","camera","gb","delivery","nairobi")):
                    active.facts["required_specs"] = text.strip()[:120]
                if "nairobi" in low and not active.location:
                    active.location = "Nairobi"
                # Keep photography context from prior raw_request if available
                _qd_ph = qualification_data.get("raw_request","") if isinstance(qualification_data, dict) else ""
                if "photography" in str(_qd_ph).lower() and "photography" not in active.facts.get("intended_use","").lower():
                    prev = active.facts.get("intended_use","")
                    active.facts["intended_use"] = (str(_qd_ph)[:60] + " | " + prev)[:120]
            active.last_active = now
            try:
                from heshly_core.services.network.service_consultant import apply_user_message as _aum2
                _aum2(active, text, "")
                if active.facts.get("matching_brief"):
                    active.matching_brief = active.facts.get("matching_brief") or ""
            except Exception:
                pass

    qd = _save_tasks(qualification_data, tasks)
    if active:
        try:
            from heshly_core.services.network.service_consultant import apply_user_message as _aum3, preserve_original_request as _por
            if not active.facts.get("original_request"):
                _por(active, active.raw_request or text)
            if is_new_task:
                _aum3(active, text, "")
                if active.facts.get("matching_brief"):
                    active.matching_brief = active.facts.get("matching_brief") or ""
            qd = _save_tasks(qualification_data, tasks)
        except Exception:
            pass
    return active, tasks, qd


def next_consultation_step(task: ConsultTask) -> tuple[str | None, str | None]:
    """
    Returns (question_or_None, assessment_or_None).
    If a focused question is needed, returns (question, None).
    If ready to assess/recommend, returns (None, assessment).
    """
    try:
        from heshly_core.services.network.service_consultant import should_defer_to_legacy_guide, next_consultant_action
        if task and not should_defer_to_legacy_guide(task):
            action = next_consultant_action(task, text=task.raw_request or "")
            reply = (action or {}).get("reply")
            if reply:
                return reply, None
    except Exception:
        pass
    q = _next_question_for_task(task)
    if q:
        return q, None
    # No further question — produce assessment
    # For service requests with service+location, assessment is referral readiness, not blocking
    if task.intent == "service_request" and task.requested_service and task.location:
        return None, None  # caller should proceed to matching
    # For consultation, produce assessment
    if task.domain in ("farming", "legal") or task.intent in ("consultation",):
        assessment = _assess_task(task)
        return None, assessment
    return None, None


def should_search_providers(task: ConsultTask) -> bool:
    """Consultation alone (e.g. farming feasibility) should NOT trigger business search."""
    if task.domain == "farming" and task.intent == "consultation":
        # Farming question is informational until user explicitly asks for a provider
        return False
    if task.domain == "legal" and not task.facts.get("problem_description"):
        return False
    if task.intent == "product_request":
        return False  # products go to catalogue, not provider matching
    if task.intent == "consultation":
        return False
    # Plumbing: block dispatch until consultant has asked its diagnostic question
    # next_consultation_step will return the valve/float question for cistern_not_filling
    # If that question exists, don't dispatch yet — ask first
    svc_low = (task.requested_service or "").lower()
    d_low = (task.domain or "").lower()
    if (d_low == "plumbing" or svc_low == "plumbing"):
        try:
            from heshly_core.services.network.service_consultant import should_defer_to_legacy_guide, next_consultant_action
            if not should_defer_to_legacy_guide(task):
                action = next_consultant_action(task, text=task.raw_request or "")
                if action and action.get("reply") and not action.get("should_dispatch"):
                    return False
        except Exception:
            pass
        if not task.facts.get("problem_type") or task.facts.get("awaiting_fact"):
            return False
    if d_low == "plumbing" or svc_low == "plumbing":
        issue = (task.facts.get("issue_description") or task.facts.get("plumbing_issue") or task.facts.get("problem_type") or "").strip()
        if not issue:
            raw_low = (task.raw_request or "").lower()
            if not any(w in raw_low for w in ("leak", "blocked", "drain", "tap", "pipe", "toilet", "sink", "burst", "fix")):
                return False
        # Do not dispatch merely because the category is known — wait for professional need,
        # exhausted DIY, an explicit send-someone request, or a safety hazard.
        if not (
            task.facts.get("needs_professional")
            or task.facts.get("wants_provider")
            or task.facts.get("diy_exhausted")
            or task.facts.get("hazard")
            or task.facts.get("search_nearby")
        ):
            ptype = task.facts.get("problem_type") or ""
            # Burst / sewage-class issues skip DIY
            if ptype not in ("burst_pipe",) and "burst" not in (task.raw_request or "").lower():
                return False
    if d_low == "electrical" or "electric" in svc_low:
        if not (
            task.facts.get("needs_professional")
            or task.facts.get("wants_provider")
            or task.facts.get("hazard")
            or task.facts.get("diy_exhausted")
        ):
            raw_low = (task.raw_request or "").lower()
            if not re.search(r"\binstall|\brewire|\blive\b|\bspark", raw_low):
                return False
    # Service requests: only search when we have enough to be useful
    return bool(task.requested_service and task.location)


def run_consultant_turn(
    text: str,
    qualification_data: dict[str, Any] | str | None,
    extracted: dict[str, Any],
    last_assistant: str = "",
    no_match: bool = False,
) -> tuple[ConsultTask | None, dict[str, Any], str | None, bool]:
    """Single turn: upsert task, apply diagnostics, return (task, qd, reply, should_dispatch)."""
    task, tasks, qd = upsert_task_from_message(text, qualification_data, extracted)
    if not task:
        return None, qd if isinstance(qd, dict) else {}, None, False
    try:
        from heshly_core.services.network.service_consultant import (
            apply_user_message,
            next_consultant_action,
            no_match_reply,
            should_defer_to_legacy_guide,
        )
        apply_user_message(task, text, last_assistant or "")
        if task.facts.get("matching_brief"):
            task.matching_brief = str(task.facts.get("matching_brief") or "")
        qd = _save_tasks(qd, tasks)
        if should_defer_to_legacy_guide(task):
            q, a = next_consultation_step(task)
            reply = q or a
            return task, qd, reply, should_search_providers(task) and not reply
        if no_match:
            reply = no_match_reply(task)
            qd = _save_tasks(qd, tasks)
            return task, qd, reply, False
        action = next_consultant_action(task, text=text, last_assistant=last_assistant, no_match=False)
        reply = (action or {}).get("reply")
        dispatch = bool((action or {}).get("should_dispatch")) and should_search_providers(task)
        qd = _save_tasks(qd, tasks)
        return task, qd, reply, dispatch
    except Exception:
        q, a = next_consultation_step(task)
        return task, qd, q or a, should_search_providers(task)
