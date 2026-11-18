"""Isolated matching/routing engine — reads existing tenant data, no new source of truth."""

from __future__ import annotations

import re
from typing import Any

from heshly_core.models.network import CandidateScore

DEFAULT_WEIGHTS = {
    "service_match": 40,
    "location": 20,
    "availability": 15,
    "reliability": 10,
    "price": 10,
    "recency_penalty": 5,
}


def _semantic_service_tokens(requested: str) -> list[str]:
    """Expand understood service phrase into semantic tokens for flexible matching without giant alias dict.
    e.g. "fridge repair" -> ["fridge","refrigerator","appliance"], "CCTV installation" -> ["cctv","camera","security"]
    Minimal, offline, no LLM key. Generic filler tokens like 'services'/'installation' are filtered.
    """
    _GENERIC_TOKENS = {"services", "service", "installation", "install", "installing", "provider", "providers", "general", "systems", "system"}
    r = (requested or "").strip().lower()
    mapping: dict[str, list[str]] = {
        "fridge": ["fridge", "refrigerator", "appliance"],
        "refrigerator": ["fridge", "refrigerator", "appliance"],
        "cctv": ["cctv", "camera", "security", "surveillance"],
        "camera": ["cctv", "camera", "security"],
        "solar": ["solar", "renewable", "energy", "power"],
        "borehole": ["borehole", "water", "drilling"],
        "architect": ["architect", "building", "construction", "design"],
        "engineer": ["engineer", "architect", "building", "construction", "structural"],
        "structural": ["structural", "engineer", "architect", "building", "construction"],
        "moving": ["moving", "mover", "relocation", "transport"],
        "mover": ["moving", "mover", "relocation"],
        "appliance": ["fridge", "refrigerator", "appliance", "electrical"],
        "dental": ["dental", "dentist", "teeth", "cleaning", "tooth", "clinic"],
        "dentist": ["dental", "dentist", "teeth", "clinic"],
        "accountant": ["accountant", "accounting", "bookkeeping", "tax", "audit", "finance"],
        "accounting": ["accountant", "accounting", "tax", "finance"],
        "lawyer": ["lawyer", "legal", "advocate", "attorney"],
        "plumbing": ["plumbing", "plumber", "pipes", "drainage", "leak"],
        "plumber": ["plumbing", "plumber", "pipes", "leak"],
        "mechanic": ["mechanic", "garage", "automotive", "vehicle", "auto"],
        "venue": ["venue", "event", "hall", "conference", "banquet"],
        "salon": ["salon", "beauty", "hair", "barber"],
        "clinic": ["clinic", "hospital", "medical", "health"],
        "venue": ["venue", "event", "hall", "conference", "banquet", "meeting"],
        "event venue": ["venue", "event", "hall", "conference"],
        "event": ["venue", "event", "hall"],
        "hall": ["venue", "event", "hall"],

    }
    out: set[str] = set()
    for key, syns in mapping.items():
        if key in r:
            out.update(syns)
    # Also add the raw substantive tokens (skip generic filler)
    for tok in [t for t in r.split() if len(t) > 2 and t not in _GENERIC_TOKENS]:
        out.add(tok)
    filtered = [t for t in out if t not in _GENERIC_TOKENS]
    return filtered if filtered else [t for t in r.split() if len(t) > 2 and t not in _GENERIC_TOKENS]


def _semantic_service_score(requested: str | None, services_text: str | None) -> tuple[float, str]:
    """Semantic service score: understands intent, e.g. "fridge isn't cooling" -> fridge/appliance repair."""
    if not requested:
        return _service_score(requested, services_text)
    if not services_text:
        return 0.2, "business has no services listed"
    # Try exact then semantic
    base_score, base_reason = _service_score(requested, services_text)
    if base_score > 0.5:
        return base_score, base_reason + " (direct)"
    # Semantic: expand requested into intent tokens
    s = services_text.lower()
    tokens = _semantic_service_tokens(requested)
    if not tokens:
        return base_score, base_reason
    hits = sum(1 for t in tokens if len(t) > 2 and t in s)
    if hits:
        # Semantic hit — treat as partial relevance, not hard mismatch
        sem_score = 0.55 + 0.25 * (hits / max(len(tokens), 1))
        return min(0.85, sem_score), f"semantic match '{requested}' ~ '{services_text[:40]}' ({hits}/{len(tokens)} tokens)"
    return base_score, base_reason + " (semantic miss)"


def _service_score(requested: str | None, services_text: str | None) -> tuple[float, str]:
    if not requested:
        return 0.5, "no service requested"
    if not services_text:
        return 0.2, "business has no services listed"
    _GENERIC_TOKENS = {"services", "service", "installation", "install", "installing", "provider", "providers", "general", "systems", "system"}
    r = requested.lower().strip()
    s = services_text.lower()
    if r in s:
        # Guard: exact substring match that is solely a generic word should not count
        # e.g. 'services' alone would otherwise match every "X services" business
        if r in _GENERIC_TOKENS:
            return 0.1, "service not matched (generic token)"
        return 1.0, f"service '{requested}' matched"
    # partial token match — ignore generic filler tokens (services, installation, etc.)
    tokens = [t for t in r.split() if len(t) > 2 and t not in _GENERIC_TOKENS]
    if not tokens:
        return 0.1, "service not matched (no substantive tokens)"
    hits = sum(1 for t in tokens if t in s)
    if hits:
        return 0.6 + 0.2 * (hits / max(len(tokens), 1)), f"partial match {hits}/{len(tokens)}"
    return 0.1, "service not matched"


def _is_eligible_service(requested: str | None, services_text: str | None) -> bool:
    """Service eligibility: semantic — request understood, not whitelist.
    If business has no service data, allow (geography still gates). If we have semantic match, allow even for open-ended service.
    """
    if not requested or not str(requested).strip():
        return True  # No service constraint → no restriction
    # Prohibited intent is disqualified earlier at qualification, not here
    if str(requested).strip() == "__prohibited__":
        return False
    if not services_text or not str(services_text).strip():
        # No service data on business -> don't block on service, location still gates
        return True

    # Try semantic score — open-ended matching without hard whitelist
    sem_score, _ = _semantic_service_score(requested, services_text)
    # Keep a lenient threshold: 0.4+ passes. This lets "fridge repair" match "Appliance repair" etc.
    return sem_score >= 0.4


_NEARBY_PARENTS: dict[str, list[str]] = {
    "mwiki": ["kasarani", "nairobi", "roysambu"],
    "kasarani": ["nairobi", "mwiki", "roysambu", "githurai"],
    "roysambu": ["nairobi", "kasarani", "mwiki"],
    "westlands": ["nairobi", "parklands", "chiromo"],
    "chiromo": ["westlands", "nairobi"],
    "parklands": ["westlands", "nairobi"],
    "kayole": ["nairobi", "embakasi"],
    "embakasi": ["nairobi", "kayole"],
    "ruiru": ["nairobi", "thika", "juja"],
    "thika": ["ruiru", "nairobi"],
    "kitengela": ["nairobi", "athiriver"],
    "syokimau": ["nairobi", "mlolongo", "athiriver"],
}


def _location_search_tokens(requested_loc: str, nearby: bool = False) -> list[str]:
    rl = (requested_loc or "").strip().lower()
    if not rl:
        return []
    parts = [p.strip() for p in re.split(r"[,/]| and ", rl) if len(p.strip()) >= 3]
    tokens = list(parts) if parts else [rl]
    if nearby:
        extra: list[str] = []
        for t in list(tokens):
            extra.extend(_NEARBY_PARENTS.get(t, []))
            for key, parents in _NEARBY_PARENTS.items():
                if key in t:
                    extra.extend(parents)
        tokens.extend(extra)
        # County-level fallback once the customer agreed to expand
        if "nairobi" not in tokens:
            tokens.append("nairobi")
    # unique, keep order
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _is_eligible_location(requested_loc: str | None, biz_location: str | None, service_area: str | None, nearby: bool = False) -> bool:
    """Geographic eligibility: True if location constraint satisfied or no constraint."""
    if not requested_loc:
        return True  # Rule F: no location → no restriction
    rl = requested_loc.strip().lower()
    if not rl:
        return True
    needles = _location_search_tokens(rl, nearby=nearby) or [rl]
    for loc in [service_area, biz_location]:
        if not loc:
            continue
        ll = loc.lower().strip()
        for n in needles:
            if n in ll or ll in n:
                return True
    return False


def _location_score(requested_loc: str | None, biz_location: str | None, service_area: str | None) -> tuple[float, str]:
    if not requested_loc:
        return 0.7, "no location requested"
    if not biz_location and not service_area:
        return 0.4, "business location unknown"
    rl = requested_loc.lower()
    for loc in [biz_location, service_area]:
        if loc and rl in loc.lower():
            return 1.0, f"location '{requested_loc}' matched"
        if loc and loc.lower() in rl:
            return 1.0, "location overlap"
    return 0.2, "location not matched"


def _availability_score(is_active: bool, hours_enabled: bool | None, accepts: bool) -> tuple[float, str]:
    if not is_active:
        return 0.0, "business inactive"
    if not accepts:
        return 0.0, "not accepting network leads"
    if hours_enabled is False:
        return 0.3, "outside business hours"
    return 1.0, "available"


def filter_eligible_candidates(
    conversation: Any,
    memberships: list[Any],
    business_map: dict[str, Any] | None = None,
    knowledge_map: dict[str, Any] | None = None,
    # Optional ConsultTask override — when provided, its service/location take precedence
    consult_task: Any | None = None,
) -> list[Any]:
    """Eligibility gate: requested service and location must both be satisfied."""
    def _g(obj: Any, key: str, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # Task-aware: if consult_task has its own service/location, use it (do not fall back to conversation)
    req_location = _g(consult_task, "location") if consult_task is not None else None
    req_service = _g(consult_task, "requested_service") if consult_task is not None else None
    req_brief = ""
    nearby = False
    if consult_task is not None:
        facts = _g(consult_task, "facts") or {}
        if isinstance(facts, dict):
            req_brief = str(facts.get("matching_brief") or "")
            nearby = bool(facts.get("search_nearby"))
        req_brief = req_brief or str(_g(consult_task, "matching_brief") or "")
    # Fallback to conversation only if task provided no value (backward compat + location-less tasks)
    if req_location in (None, ""):
        req_location = _g(conversation, "location")
    if req_service in (None, ""):
        req_service = _g(conversation, "requested_service")
    # matching_brief is ranking-only; eligibility stays on the service category

    business_map = business_map or {}
    knowledge_map = knowledge_map or {}

    eligible: list[Any] = []

    for m in memberships:
        tenant_id = _g(m, "tenant_id") or ""
        business_id = _g(m, "business_id") or tenant_id

        biz = business_map.get(tenant_id) or business_map.get(business_id) or {}
        biz_location = _g(biz, "location")
        service_area = _g(m, "service_area")

        km = knowledge_map.get(tenant_id) or knowledge_map.get(business_id)
        if km is not None:
            if isinstance(km, dict):
                services_text = km.get("services") or km.get("services_text")
            else:
                services_text = getattr(km, "services", None)
        else:
            services_text = None

        # Service is a hard eligibility constraint when service data was supplied.
        # If knowledge_map is omitted, preserve the historical geographic-only behavior.
        if knowledge_map and not _is_eligible_service(req_service, services_text):
            continue

        # Location is a hard eligibility constraint when the customer specified one.
        if not _is_eligible_location(
            str(req_location) if req_location and str(req_location).strip() else None,
            biz_location,
            service_area,
            nearby=nearby,
        ):
            continue

        eligible.append(m)

    return eligible


def rank_candidates(
    conversation: Any,
    memberships: list[Any],
    business_map: dict[str, Any] | None = None,
    knowledge_map: dict[str, Any] | None = None,
    hours_map: dict[str, bool | None] | None = None,
    weights: dict[str, float] | None = None,
    consult_task: Any | None = None,
) -> list[CandidateScore]:
    """
    Pure ranking — caller supplies memberships + optional enrichment maps.
    When consult_task provided, its service/location/budget override conversation.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    total_w = w["service_match"] + w["location"] + w["availability"] + w["reliability"] + w["price"]

    def _g(obj: Any, key: str, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # Task-aware override
    _g_task = lambda k: _g(consult_task, k) if consult_task is not None else None
    req_service = _g_task("requested_service") if consult_task is not None and _g_task("requested_service") not in (None, "") else _g(conversation, "requested_service")
    req_location = _g_task("location") if consult_task is not None and _g_task("location") not in (None, "") else _g(conversation, "location")
    req_brief = ""
    rank_nearby = False
    if consult_task is not None:
        _tf = _g_task("facts") or {}
        if isinstance(_tf, dict):
            req_brief = str(_tf.get("matching_brief") or "")
            rank_nearby = bool(_tf.get("search_nearby"))
        req_brief = req_brief or str(_g_task("matching_brief") or "")
    rank_service = " ".join(p for p in (str(req_service or ""), req_brief) if p).strip() or req_service
    budget_min = _g_task("budget_min") if consult_task is not None and _g_task("budget_min") is not None else _g(conversation, "budget_min")
    budget_max = _g_task("budget_max") if consult_task is not None and _g_task("budget_max") is not None else _g(conversation, "budget_max")

    business_map = business_map or {}
    knowledge_map = knowledge_map or {}
    hours_map = hours_map or {}

    results: list[CandidateScore] = []
    for m in memberships:
        tenant_id = _g(m, "tenant_id") or ""
        business_id = _g(m, "business_id") or tenant_id
        accepts = bool(_g(m, "accepts_network_leads", True))
        status = str(_g(m, "status", "Active"))
        is_active = status.lower() == "active"
        reliability = float(_g(m, "reliability_score", 100) or 0)
        service_area = _g(m, "service_area")

        biz = business_map.get(tenant_id) or business_map.get(business_id) or {}
        biz_location = _g(biz, "location")
        biz_status = _g(biz, "status", "Active")
        if str(biz_status).lower() != "active":
            is_active = False

        knowledge_text = None
        km = knowledge_map.get(tenant_id) or knowledge_map.get(business_id)
        if km is not None:
            if isinstance(km, dict):
                knowledge_text = km.get("services") or km.get("services_text")
            else:
                knowledge_text = getattr(km, "services", None)

        hours_enabled = hours_map.get(tenant_id)
        if hours_enabled is None:
            hours_enabled = hours_map.get(business_id)

        s_svc, r_svc = _semantic_service_score(rank_service, knowledge_text)
        s_loc, r_loc = _location_score(req_location, biz_location, service_area)
        if rank_nearby and s_loc < 0.5:
            # Nearby search: score parent-area overlap instead of treating it as a hard miss
            for tok in _location_search_tokens(str(req_location or ""), nearby=True):
                blob = f"{biz_location or ''} {service_area or ''}".lower()
                if tok and tok in blob:
                    s_loc, r_loc = 0.7, f"nearby area match '{tok}'"
                    break
        s_avail, r_avail = _availability_score(is_active, hours_enabled, accepts)
        # reliability normalized 0-1
        s_rel = max(0.0, min(1.0, reliability / 100.0))
        r_rel = f"reliability {reliability:.0f}"
        # price: neutral unless budget provided; check lead_fee within budget
        s_price = 0.7
        r_price = "no budget constraint"
        lead_fee = _g(m, "lead_fee")
        if budget_min is not None or budget_max is not None:
            try:
                fee = float(lead_fee or 0)
                if budget_max is not None and fee > float(budget_max):
                    s_price = 0.2
                    r_price = f"fee {fee} exceeds budget max {budget_max}"
                elif budget_min is not None and fee < float(budget_min) * 0.5:
                    s_price = 0.8
                    r_price = "fee well within budget"
            except Exception:
                pass

        if s_avail == 0.0:
            score = 0.0
        else:
            score = (
                s_svc * w["service_match"]
                + s_loc * w["location"]
                + s_avail * w["availability"]
                + s_rel * w["reliability"]
                + s_price * w["price"]
            ) / total_w

        reasons = {
            "service": r_svc,
            "location": r_loc,
            "availability": r_avail,
            "reliability": r_rel,
            "price": r_price,
            "weights": w,
        }
        results.append(CandidateScore(tenant_id=tenant_id, business_id=business_id, score=round(score, 4), reasons=reasons))

    results.sort(key=lambda c: c.score, reverse=True)
    return results


def enrich_from_frappe(memberships: list[Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, bool | None]]:
    """Optional Frappe-enriched maps (best-effort, never raises). Used by service layer."""
    business_map: dict[str, Any] = {}
    knowledge_map: dict[str, Any] = {}
    hours_map: dict[str, bool | None] = {}
    try:
        import frappe  # type: ignore
        for m in memberships:
            tid = getattr(m, "tenant_id", None) or (m.get("tenant_id") if isinstance(m, dict) else None)
            if not tid:
                continue
            try:
                biz = frappe.db.get_value("Business Account", {"tenant_id": tid}, ["business_id", "location", "status"], as_dict=True)
                if biz:
                    business_map[tid] = biz
            except Exception:
                pass
            try:
                kp = frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tid}, ["services"], as_dict=True)
                if kp:
                    knowledge_map[tid] = kp
            except Exception:
                pass
            hours_map[tid] = None  # hours check is external; keep None to mean unknown/assumed open
    except Exception:
        pass
    return business_map, knowledge_map, hours_map
