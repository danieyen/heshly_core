"""Domain-aware first-line service consultant.

Used by consultation_engine — not a parallel chatbot. It enriches ConsultTask
facts (problem type, diagnostic history, matching brief) and returns the next
useful reply. Matching and dispatch stay in the existing engines.
"""

from __future__ import annotations

import re
from typing import Any


_YES_RE = re.compile(
    r"^\s*(?:yes|yeah|yep|yup|ok|okay|sure|please|alright|all\s+right|go\s+ahead|fine|do\s+it|please\s+do)"
    r"(?:\s*[,.!]|\s+but\b|\s+and\b|\s*$)",
    re.I,
)
_NO_RE = re.compile(r"^\s*(?:no|nope|nah|not\s+really|don't|do\s+not)\b", re.I)
_ADVICE_RE = re.compile(
    r"\b(?:advice|advise|consultant|consult|diagnose|troubleshoot|what\s+should\s+i\s+(?:do|check|try)|"
    r"how\s+(?:can|do)\s+i\s+(?:fix|check|unclog|stop)|act\s+like|help\s+me\s+understand|"
    r"what(?:'s|\s+is)\s+wrong|can\s+you\s+help\s+me\s+(?:figure|understand)|diy|"
    r"before\s+(?:we\s+)?(?:call|hire|book))\b",
    re.I,
)
_SEND_PROVIDER_RE = re.compile(
    r"\b(?:send\s+(?:them|someone|a\s+plumber|an?\s+\w+)|find\s+(?:me\s+)?(?:someone|a\s+provider|a\s+plumber)|"
    r"book\s+(?:them|someone)|dispatch|look\s+for\s+(?:someone|a\s+plumber|options)|"
    r"check\s+nearby|nearby\s+areas?|still\s+(?:need|want)\s+(?:someone|a\s+professional))\b",
    re.I,
)
_NEARBY_RE = re.compile(r"\bnearby\b|\bcheck\s+(?:other\s+)?areas?\b|\bbroader\s+area\b|\bsurrounding\b", re.I)

_HAZARD_RULES: list[tuple[str, re.Pattern, str]] = [
    (
        "gas",
        re.compile(r"\bgas\s+leak\b|\bsmell(?:s|ing)?\s+gas\b|\bgas\s+odour\b|\bgas\s+odor\b", re.I),
        "If you smell gas, leave the building if it is safe to do so, avoid switches and flames, and get a licensed gas professional immediately. I will not walk you through any gas-pipe work.",
    ),
    (
        "electrical_live",
        re.compile(r"\bspark(?:s)?\b|\bburning\s+smell\b|\belectric\s+shock\b|\blive\s+wire\b|\bwires?\s+(?:are\s+)?exposed\b|\bsmoke\s+from\b", re.I),
        "That sounds electrically unsafe. Do not touch wiring or open fittings. If you can do so safely, switch off the relevant breaker, stay clear, and we should get a qualified electrician.",
    ),
    (
        "flooding",
        re.compile(r"\bflooding\b|\bwater\s+everywhere\b|\bceiling\s+(?:is\s+)?(?:dripping|collaps)|water\s+coming\s+through\s+the\s+ceiling", re.I),
        "With active flooding, the priority is stopping more water if you can safely reach the isolation valve or mains tap — then a professional. Do not open pressurised pipes yourself.",
    ),
    (
        "sewage",
        re.compile(r"\bsewage\b|\boverflowing\s+toilet\b|\bwaste\s+water\s+on\s+(?:the\s+)?floor\b|\bfaecal\b|\bfecal\b", re.I),
        "Sewage on the floor is a health hazard. Avoid contact, keep others away, and get a plumber rather than forcing the toilet or mixing drain chemicals.",
    ),
    (
        "structural",
        re.compile(r"\bcollaps|\bceiling\s+coming\s+down\b|\blarge\s+crack\b|\bsagging\s+beam\b", re.I),
        "That may be a structural risk. Keep clear of the affected area and involve a qualified professional rather than forcing anything.",
    ),
]


def is_contextual_affirmative(text: str | None) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if _ADVICE_RE.search(t) and _YES_RE.search(t):
        return True
    if len(t) > 80 and not _YES_RE.match(t):
        return False
    return bool(_YES_RE.match(t))


def is_contextual_negative(text: str | None) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return bool(_NO_RE.match(t)) and not re.search(r"\bno\s+not\s+a\b", t, re.I)


def is_advice_request(text: str | None) -> bool:
    return bool(_ADVICE_RE.search(text or ""))


def is_provider_request(text: str | None) -> bool:
    return bool(_SEND_PROVIDER_RE.search(text or ""))


def is_nearby_request(text: str | None, last_assistant: str = "") -> bool:
    t = text or ""
    if _NEARBY_RE.search(t):
        return True
    if is_contextual_affirmative(t) and _NEARBY_RE.search(last_assistant or ""):
        return True
    return False


def _hist(task: Any) -> list[dict[str, str]]:
    f = task.facts
    hist = f.get("diagnostic_history")
    if not isinstance(hist, list):
        hist = []
        f["diagnostic_history"] = hist
    return hist


def _note(task: Any, key: str, value: Any) -> None:
    task.facts[key] = value


def _append_hist(task: Any, role: str, text: str) -> None:
    hist = _hist(task)
    if text:
        hist.append({"role": role, "text": text[:240]})
        if len(hist) > 24:
            del hist[:-24]


def preserve_original_request(task: Any, text: str) -> None:
    f = task.facts
    raw = (text or "").strip()
    if not f.get("original_request"):
        seed = (task.raw_request or raw or task.desired_outcome or "").strip()
        if seed and not is_contextual_affirmative(seed) and seed.lower() not in ("yes", "no", "ok"):
            f["original_request"] = seed[:200]
    if raw and not is_contextual_affirmative(raw) and not is_advice_request(raw) and len(raw) > 8:
        # Refine, never replace the original
        if "toilet" in raw.lower() or "cistern" in raw.lower() or "leak" in raw.lower() or "not filling" in raw.lower():
            f["refined_request"] = raw[:200]


def detect_hazard(text: str) -> tuple[str, str] | None:
    for code, pat, msg in _HAZARD_RULES:
        if pat.search(text or ""):
            return code, msg
    return None


# ---------------------------------------------------------------------------
# Problem identification (plumbing and other trades)
# ---------------------------------------------------------------------------

_PLUMBING_PROBLEMS: list[tuple[str, re.Pattern, str]] = [
    ("blocked_toilet", re.compile(r"blocked\s+toilet|clogged\s+toilet|toilet.{0,30}(blocked|clogged)|won't\s+go\s+down|water\s+(?:not\s+going\s+down|isn't\s+draining|is\s+not\s+draining|not\s+draining|stays\s+in\s+the\s+bowl)|the\s+toilet\s+won't\s+flush|draining\s+very\s+slowly|keeps?\s+filling\s+up|won't\s+flush", re.I), "blocked toilet"),
    ("cistern_not_filling", re.compile(r"cistern.{0,40}(not\s+filling|won'?t\s+fill|empty|no\s+water)|(?:tank|cistern).{0,20}(?:isn'?t|not)\s+fill|(?:not\s+filling|no\s+water\s+in\s+(?:the\s+)?(?:cistern|tank))", re.I), "toilet cistern not filling"),
    ("running_toilet", re.compile(r"running\s+toilet|keeps?\s+running|won'?t\s+stop\s+(?:running|flushing)|continuously\s+running", re.I), "continuously running toilet"),
    ("leaking_cistern", re.compile(r"leaking\s+cistern|cistern\s+leak|water\s+from\s+(?:the\s+)?(?:cistern|tank)", re.I), "leaking cistern"),
    ("flush_mechanism", re.compile(r"flush\s+(?:button|handle|mechanism)|won'?t\s+flush|does(?:n'?t| not)\s+flush", re.I), "flush mechanism not releasing water"),
    ("blocked_drain", re.compile(r"blocked\s+drain|clogged\s+drain|slow\s+drain", re.I), "blocked drain"),
    ("burst_pipe", re.compile(r"\bburst\b", re.I), "burst pipe"),
    ("tap_leak", re.compile(r"tap\s+(?:leak|drip)|leaking\s+tap|dripping\s+tap|faucet", re.I), "leaking tap"),
    ("pipe_leak", re.compile(r"leaking\s+pipe|pipe\s+leak|under\s+the\s+sink", re.I), "leaking pipe"),
    ("toilet_unspecified", re.compile(r"\btoilet\b", re.I), "toilet problem"),
]

_ELECTRICAL_PROBLEMS: list[tuple[str, re.Pattern, str]] = [
    ("no_power_area", re.compile(r"no\s+power|tripped|breaker|fuse|lights?\s+(?:are\s+)?out|power\s+cut", re.I), "power outage or tripped circuit"),
    ("outlet_dead", re.compile(r"socket|outlet|plug\s+(?:point|not\s+working)", re.I), "dead socket"),
    ("appliance_no_power", re.compile(r"not\s+coming\s+on|won't\s+turn\s+on|no\s+power", re.I), "appliance without power"),
    ("wiring", re.compile(r"wir(?:ing|es)|install(?:ation)?", re.I), "electrical installation or wiring"),
]

_APPLIANCE_PROBLEMS: list[tuple[str, re.Pattern, str]] = [
    ("not_cooling", re.compile(r"not\s+cool(?:ing)?|not\s+getting\s+cold|warm", re.I), "appliance not cooling"),
    ("not_heating", re.compile(r"not\s+heat(?:ing)?|no\s+hot\s+water|cold\s+water\s+only", re.I), "not heating"),
    ("not_starting", re.compile(r"won'?t\s+start|not\s+starting|dead", re.I), "appliance not starting"),
    ("noisy", re.compile(r"noise|noisy|loud|grinding", re.I), "unusual noise"),
    ("leaking_appliance", re.compile(r"leak", re.I), "appliance leak"),
]

_CLEANING_PROBLEMS: list[tuple[str, re.Pattern, str]] = [
    ("stain", re.compile(r"\b(?:stain|spill|mark)\b", re.I), "stain removal"),
    ("deep_clean", re.compile(r"deep\s+clean|after\s+renovation|move[\s-]?out", re.I), "deep cleaning"),
    ("carpet", re.compile(r"carpet|upholstery|sofa", re.I), "carpet or upholstery cleaning"),
]


def _match_problem(text: str, table: list[tuple[str, re.Pattern, str]]) -> tuple[str, str] | None:
    for code, pat, label in table:
        if pat.search(text or ""):
            return code, label
    return None


_WATER_HEATER_PROBLEMS: list[tuple[str, re.Pattern, str]] = [
    ("water_heater_leak", re.compile(r"water\s*heater.*\b(?:leak|leaking|drip|water\s+on\s+the\s+floor)\b|\bleak.*water\s*heater|\bgeyser.*\bleak", re.I), "water heater leaking"),
    ("water_heater_safety", re.compile(r"water\s*heater.*\b(?:spark|shock|burning\s+smell|gas\s+smell|smell\s+gas)\b|\b(?:spark|shock|burning\s+smell|gas\s+smell).*water\s*heater", re.I), "water heater safety hazard"),
    ("water_heater_not_heating", re.compile(r"water\s*heater.*\b(?:not\s+heating|isn'?t\s+heating|not\s+heat|no\s+hot\s+water|cold\s+water\s+only|not\s+getting\s+hot)\b", re.I), "water heater not heating"),
    ("water_heater_no_hot_water", re.compile(r"\bno\s+hot\s+water\b|\bcold\s+water\s+only\b", re.I), "no hot water"),
]

def identify_problem(task: Any, text: str) -> None:
    domain = (task.domain or "").lower()
    svc = (task.requested_service or "").lower()
    blob = " ".join(
        x for x in (
            text,
            task.raw_request,
            task.desired_outcome,
            task.facts.get("original_request"),
            task.facts.get("refined_request"),
            task.facts.get("issue_description"),
        ) if x
    )
    # Water-heater must be detected before generic plumbing/appliance fallback
    wh = _match_problem(blob, _WATER_HEATER_PROBLEMS)
    if wh:
        code, label = wh
        task.facts["problem_type"] = code
        task.facts["problem_label"] = label
        task.facts["issue_description"] = label
        task.facts["trade_family"] = "water_heater"
        _refresh_matching_brief(task)
        return
    found = None
    if domain in ("water_heater",) or "water heater" in svc or "geyser" in svc:
        found = _match_problem(blob, _WATER_HEATER_PROBLEMS)
        if found:
            task.facts["trade_family"] = "water_heater"
    if not found and (domain == "plumbing" or "plumb" in svc or "toilet" in blob.lower() or "drain" in blob.lower()):
        found = _match_problem(blob, _PLUMBING_PROBLEMS)
    elif domain == "electrical" or "electric" in svc:
        found = _match_problem(blob, _ELECTRICAL_PROBLEMS)
    elif domain in ("general_service", "general") and re.search(r"fridge|washer|cooker|oven|microwave|ac\b|air.?con", blob, re.I):
        found = _match_problem(blob, _APPLIANCE_PROBLEMS)
        if found:
            task.facts["trade_family"] = "appliances"
    elif domain in ("general_service", "general", "cleaning") or "clean" in svc:
        found = _match_problem(blob, _CLEANING_PROBLEMS)
        if found:
            task.facts["trade_family"] = "cleaning"
    if found:
        code, label = found
        prev = task.facts.get("problem_type")
        if not prev or prev == "toilet_unspecified" or (prev != code and code != "toilet_unspecified"):
            if not (prev and prev != "toilet_unspecified" and code == "toilet_unspecified"):
                task.facts["problem_type"] = code
                task.facts["problem_label"] = label
        if not task.facts.get("issue_description") and label:
            task.facts["issue_description"] = label
        _refresh_matching_brief(task)


def _refresh_matching_brief(task: Any) -> None:
    svc = (task.requested_service or "service").strip()
    label = task.facts.get("problem_label") or task.facts.get("refined_request") or ""
    causes = task.facts.get("possible_causes") or []
    if isinstance(causes, str):
        causes = [causes]
    parts = [svc]
    if label:
        parts.append(str(label))
    if causes:
        parts.append("possible: " + ", ".join(str(c) for c in causes[:3]))
    skill = task.facts.get("required_skill")
    if skill:
        parts.append(str(skill))
    brief = "; ".join(p for p in parts if p)
    task.facts["matching_brief"] = brief[:240]
    task.facts["problem_summary"] = (label or task.facts.get("issue_description") or "")[:200]
    if label and (not task.desired_outcome or task.desired_outcome == (task.raw_request or "")[:120]):
        task.desired_outcome = str(label)[:120]


# ---------------------------------------------------------------------------
# Safety / DIY / professional gates
# ---------------------------------------------------------------------------

_IMMEDIATE_PROFESSIONAL = {
    "burst_pipe", "sewage", "flooding", "gas", "electrical_live", "structural", "wiring",
}

_DIY_OK = {
    "cistern_not_filling", "tap_leak", "running_toilet", "blocked_toilet",
    "not_starting", "no_power_area", "outlet_dead", "stain", "not_cooling",
}


def _set_causes(task: Any, *causes: str, skill: str = "") -> None:
    task.facts["possible_causes"] = list(causes)
    if skill:
        task.facts["required_skill"] = skill
    _refresh_matching_brief(task)


_BLOCKED_CONTINUATION_RE = re.compile(r"water\s+(?:not\s+going\s+down|isn't\s+draining|is\s+not\s+draining|not\s+draining|stays\s+in\s+the\s+bowl)|the\s+toilet\s+won't\s+flush|draining\s+very\s+slowly|keeps?\s+filling\s+up|won't\s+flush", re.I)

def _is_blocked_toilet_continuation(text: str) -> bool:
    return bool(_BLOCKED_CONTINUATION_RE.search(text or ""))

def apply_user_message(task: Any, text: str, last_assistant: str = "") -> None:
    """Update task facts from the latest customer message. Never discards the original request."""
    preserve_original_request(task, text)
    low = (text or "").strip()
    pending = str(task.facts.get("pending_prompt") or "")
    hazard = detect_hazard(" ".join(x for x in (low, last_assistant, task.raw_request or "") if x))
    if hazard:
        code, _msg = hazard
        task.facts["hazard"] = code
        task.facts["needs_professional"] = True
        task.facts["diy_safe"] = False

    # Water-heater safety: gas/sparks/shock/burning
    _wh_safety = task.facts.get("problem_type") in ("water_heater_safety",)
    if _wh_safety or re.search(r"water\s*heater.*(?:spark|shock|burning|gas\s+smell|smell\s+gas)", low, re.I):
        task.facts["hazard"] = "water_heater_safety"
        task.facts["needs_professional"] = True
        task.facts["diy_safe"] = False

    # Blocked-toilet natural variations: treat as same problem, not generic follow-up
    if task.facts.get("problem_type") == "blocked_toilet" and _is_blocked_toilet_continuation(low):
        task.facts["refined_request"] = low[:200]
        task.facts["issue_description"] = task.facts.get("issue_description") or low[:120]

    identify_problem(task, low)

    if is_advice_request(low):
        task.facts["wants_advice"] = True
        task.intent = task.intent or "service_request"

    if is_provider_request(low) and not is_advice_request(low):
        task.facts["wants_provider"] = True

    if is_nearby_request(low, last_assistant) or pending == "nearby":
        if is_contextual_affirmative(low) or is_nearby_request(low, last_assistant):
            task.facts["search_nearby"] = True
            task.facts["wants_provider"] = True

    # Record answer to the last diagnostic question
    qid = str(task.facts.get("awaiting_fact") or "")
    if qid and low:
        # Water-heater: heater_symptom_detail — map short answers like "completely cold"
        if qid == "heater_symptom_detail":
            if re.search(r"completely\s+cold", low, re.I) or low.strip().lower() in ("completely cold", "cold", "it is cold", "its cold"):
                task.facts[qid] = "completely cold"
            elif re.search(r"runs?\s+out|quickly|briefly.*hot", low, re.I):
                task.facts[qid] = "runs out quickly"
            elif is_contextual_negative(low):
                task.facts[qid] = "no"
            else:
                task.facts[qid] = low[:160]
        elif re.search(r"\boverflow", low, re.I):
            if re.match(r"^\s*yes\b", low, re.I) or "overflowing" in low.lower():
                task.facts[qid] = "yes"
            elif is_contextual_negative(low):
                task.facts[qid] = "no"
            else:
                task.facts[qid] = low[:160]
        elif is_contextual_affirmative(low):
            task.facts[qid] = "yes"
        elif is_contextual_negative(low):
            task.facts[qid] = "no"
        else:
            task.facts[qid] = low[:160]
        task.facts["awaiting_fact"] = ""
        _append_hist(task, "customer", low)

    # DIY result
    if pending == "diy_result":
        if is_contextual_affirmative(low) and not re.search(r"\bstill\b|\bdidn'?t\b|\bnot\b", low, re.I):
            task.facts["diy_result"] = "resolved"
        elif is_contextual_negative(low) or re.search(r"\bstill\b|\bdidn'?t\s+work\b|\bno\s+change\b|\bsame\b", low, re.I):
            task.facts["diy_result"] = "failed"
            task.facts["diy_exhausted"] = True
            task.facts["needs_professional"] = True
        else:
            task.facts["diy_result"] = low[:160]
            if re.search(r"\bstill\b|\bworse\b|\bno\s+water\b|\bnothing\b", low, re.I):
                task.facts["diy_exhausted"] = True
                task.facts["needs_professional"] = True

    ptype = task.facts.get("problem_type")
    if ptype in _IMMEDIATE_PROFESSIONAL or task.facts.get("hazard"):
        task.facts["needs_professional"] = True
        task.facts["diy_safe"] = False

    # Refine causes from answers
    if ptype == "cistern_not_filling":
        _set_causes(
            task,
            "stuck float",
            "closed water supply valve",
            "faulty fill valve",
            skill="plumber experienced in toilet cistern repairs",
        )
    elif ptype == "blocked_toilet":
        _set_causes(task, "local blockage in the pan", "blocked soil pipe", skill="plumber experienced in drain and toilet unblocking")
    elif ptype == "running_toilet":
        _set_causes(task, "worn flapper or flush valve", "high float setting", skill="plumber experienced in toilet cistern repairs")
    elif ptype == "tap_leak":
        _set_causes(task, "worn washer or cartridge", skill="plumber for tap repairs")
    elif ptype == "burst_pipe":
        _set_causes(task, "failed pipe or fitting", skill="plumber for emergency leak repair")
        task.facts["needs_professional"] = True

    if not task.facts.get("issue_description"):
        if any(w in low.lower() for w in ("leak", "blocked", "drain", "tap", "pipe", "toilet", "sink", "burst", "cistern")):
            task.facts["issue_description"] = low[:120]

    _refresh_matching_brief(task)


def _ask(task: Any, fact_key: str, question: str, pending: str = "diagnose") -> str:
    task.facts["awaiting_fact"] = fact_key
    task.facts["pending_prompt"] = pending
    _append_hist(task, "assistant", question)
    return question


def _diy(task: Any, instruction: str, why: str) -> str:
    task.facts["pending_prompt"] = "diy_result"
    task.facts["diy_offered"] = True
    msg = f"{instruction} {why} What happened after you tried that?"
    _append_hist(task, "assistant", msg)
    return msg


def _professional_needed(task: Any) -> bool:
    if task.facts.get("hazard") or task.facts.get("needs_professional"):
        return True
    if task.facts.get("diy_exhausted"):
        return True
    ptype = task.facts.get("problem_type")
    if ptype in _IMMEDIATE_PROFESSIONAL:
        return True
    if ptype in ("pipe_leak", "burst_pipe", "wiring", "leaking_cistern") and task.facts.get("diy_offered"):
        return True
    if ptype in ("pipe_leak", "burst_pipe", "wiring"):
        return True
    return False


def _safe_diy_available(task: Any) -> bool:
    if task.facts.get("diy_safe") is False:
        return False
    if task.facts.get("hazard"):
        return False
    if task.facts.get("diy_exhausted") or task.facts.get("diy_result") == "failed":
        return False
    ptype = task.facts.get("problem_type")
    if ptype in _IMMEDIATE_PROFESSIONAL:
        return False
    return ptype in _DIY_OK or task.facts.get("wants_advice")


def _intro(task: Any) -> str:
    # Water-heater and other specific diagnoses have dedicated acknowledges; suppress generic intro for them
    if task.facts.get("problem_type") in ("water_heater_not_heating", "water_heater_leak", "water_heater_no_hot_water"):
        return ""
    orig = task.facts.get("original_request") or task.desired_outcome or task.requested_service or "this"
    loc = (task.location or "").strip()
    label = task.facts.get("problem_label")
    svc = (task.requested_service or "professional").strip()
    # Suppress generic painter intro duplication
    if svc.lower() in ("painting", "painter"):
        return ""
    if label:
        base = f"Sure — I still have your request to deal with the {label}"
    else:
        short = str(orig).rstrip(".")
        if len(short) > 80:
            short = svc
        if loc and loc.lower() in short.lower():
            loc = ""
        base = f"Sure, I can help you with {short}"
    if loc:
        base += f" in {loc}"
    return base + "."


def plumbing_next(task: Any, text: str, no_match: bool = False) -> dict[str, Any]:
    ptype = task.facts.get("problem_type")
    loc = (task.location or "").strip()
    svc = (task.requested_service or "plumber").strip()

    if task.facts.get("hazard"):
        code = task.facts.get("hazard")
        msg = next((m for c, _p, m in _HAZARD_RULES if c == code), "This looks unsafe to handle yourself.")
        task.facts["pending_prompt"] = "want_provider"
        reply = msg + f" I can look for a suitable {svc}" + (f" around {loc}" if loc else "") + " as soon as you want."
        if no_match:
            reply += f" I couldn't find a listed {svc} in {loc or 'that area'} just now — I can check nearby areas while we keep this request open."
            task.facts["pending_prompt"] = "nearby"
        return {"reply": reply, "should_dispatch": bool(loc) and not no_match, "pending_prompt": task.facts["pending_prompt"]}

    # Identify unspecified toilet issues
    if ptype in (None, "toilet_unspecified") and (ptype == "toilet_unspecified" or re.search(r"\btoilet\b", " ".join([text, task.raw_request or ""]), re.I)):
        if ptype == "toilet_unspecified" or (not ptype and re.search(r"toilet.{0,20}not working|not working.{0,20}toilet|fix (my )?toilet", f"{text} {task.raw_request}", re.I)):
            if not task.facts.get("asked_toilet_kind"):
                task.facts["asked_toilet_kind"] = True
                q = (
                    f"{_intro(task)} Before we look for a plumber, I need to understand what is actually happening. "
                    "Is the toilet blocked, is the cistern not filling, does the flush not release water, "
                    "is the cistern leaking, or is it running continuously?"
                )
                return {"reply": _ask(task, "toilet_kind", q), "should_dispatch": False}

    if ptype == "cistern_not_filling":
        if not task.facts.get("supply_valve"):
            q = (
                "A cistern that will not fill is often a closed isolation valve, a stuck float, or a faulty fill valve — "
                "I cannot be certain from here. Can you see a small valve on the pipe feeding the cistern, and is it open "
                "(handle in line with the pipe)?"
            )
            return {"reply": _ask(task, "supply_valve", q), "should_dispatch": False}
        if task.facts.get("supply_valve") == "no" or str(task.facts.get("supply_valve")).lower() in ("closed", "off"):
            return {
                "reply": _diy(
                    task,
                    "If it is safe to reach, open that valve fully so it lines up with the pipe.",
                    "A closed valve simply stops water entering the cistern — no dismantling needed.",
                ),
                "should_dispatch": False,
            }
        if not task.facts.get("float_moves") and task.facts.get("diy_result") != "resolved":
            q = (
                "With the lid lifted carefully (do not force a cracked lid), does the float arm move freely, "
                "or does it feel stuck?"
            )
            return {"reply": _ask(task, "float_moves", q), "should_dispatch": False}
        if task.facts.get("float_moves") == "no" and not task.facts.get("diy_offered"):
            return {
                "reply": _diy(
                    task,
                    "Gently lift the float to see if water starts entering. If it does, the float may just have been stuck.",
                    "Do not force damaged parts or unscrew pressurised fittings.",
                ),
                "should_dispatch": False,
            }
        task.facts["needs_professional"] = True
        _set_causes(task, "stuck float", "closed supply valve", "faulty fill valve", skill="plumber experienced in toilet cistern repairs")
        reply = (
            "If the valve is open and the float is not simply stuck, a faulty fill valve is likely — "
            "that is a job for a plumber rather than a guess from here."
        )
        return _wrap_provider(task, reply, no_match)

    if ptype == "blocked_toilet":
        if task.facts.get("hazard") == "sewage":
            return _wrap_provider(task, "Because of the overflow risk, a plumber should handle this.", no_match)
        # If user directly described overflow/blocked variation without being asked, record it
        if not task.facts.get("overflowing") and _is_blocked_toilet_continuation(text) and "overflow" not in text.lower():
            task.facts["overflowing"] = "no"  # slow drain, not overflowing — try DIY
        if not task.facts.get("overflowing"):
            # Also handle "yes, water is close to overflowing" as confirmation in the same message
            if re.search(r"overflow", text or "", re.I) and re.search(r"^\s*yes\b|close\s+to\s+overflowing", text or "", re.I):
                task.facts["overflowing"] = "yes"
                task.facts["awaiting_fact"] = ""
                task.facts["hazard"] = "sewage"
                task.facts["needs_professional"] = True
                return _wrap_provider(
                    task,
                    "If it is close to overflowing, do not keep flushing and do not pour chemical drain cleaners — mixing those is unsafe. A plumber should clear it.",
                    no_match,
                )
            q = "Is water close to overflowing from the pan, or is it sitting lower in the bowl?"
            return {"reply": _ask(task, "overflowing", q), "should_dispatch": False}
        ov = str(task.facts.get("overflowing") or "").lower()
        if ov == "yes" or "overflow" in ov:
            task.facts["hazard"] = "sewage"
            task.facts["needs_professional"] = True
            return _wrap_provider(
                task,
                "If it is close to overflowing, do not keep flushing and do not pour chemical drain cleaners — mixing those is unsafe. A plumber should clear it.",
                no_match,
            )
        if not task.facts.get("diy_offered"):
            return {
                "reply": _diy(
                    task,
                    "If the water is not overflowing, you can try a plunger on the pan for several firm plunges.",
                    "That sometimes shifts a local blockage. Do not mix drain-cleaning chemicals.",
                ),
                "should_dispatch": False,
            }
        task.facts["needs_professional"] = True
        return _wrap_provider(task, "If plunging did not clear it, the blockage is likely beyond a safe DIY fix.", no_match)

    if ptype == "running_toilet" and not task.facts.get("diy_offered"):
        return {
            "reply": _diy(
                task,
                "Lift the cistern lid carefully and see if the float is sitting low enough to close the fill valve. If a chain or flapper is caught open, unhook it gently.",
                "A stuck flapper often causes a continuous run. Do not force cracked plastic.",
            ),
            "should_dispatch": False,
        }

    if ptype == "tap_leak" and not task.facts.get("diy_offered"):
        return {
            "reply": _diy(
                task,
                "Check the tap is firmly closed. If a spout drip continues, that is usually a washer or cartridge.",
                "Tightening the handle is safe; taking the tap apart under pressure is not. I can find a plumber if it still drips.",
            ),
            "should_dispatch": False,
        }

    if ptype in ("burst_pipe", "pipe_leak"):
        task.facts["needs_professional"] = True
        extra = "If you can safely reach the isolation valve or mains tap, shut the water off to limit damage. Do not open pressurised pipes."
        return _wrap_provider(task, extra, no_match)

    if ptype == "flush_mechanism" and not task.facts.get("asked_flush"):
        task.facts["asked_flush"] = True
        q = "When you press the flush, do you hear nothing at all, or does it try to flush but little water comes through?"
        return {"reply": _ask(task, "flush_behaviour", q), "should_dispatch": False}

    # Default plumbing: if we still don't know the issue
    if not task.facts.get("issue_description") and not ptype:
        q = f"{_intro(task)} What exactly is going wrong — for example a leak, a blocked drain, or a toilet that will not fill or flush?"
        return {"reply": _ask(task, "issue_description", q), "should_dispatch": False}

    if _professional_needed(task) or task.facts.get("wants_provider"):
        return _wrap_provider(task, "", no_match)

    if task.facts.get("wants_advice") and loc:
        q = "Tell me the main symptom in a sentence — blocked, empty cistern, leak, or running water — and I will talk you through the safe checks first."
        return {"reply": _ask(task, "issue_description", q), "should_dispatch": False}

    return {"reply": None, "should_dispatch": bool(svc and loc and (ptype or task.facts.get("issue_description")))}


def electrical_next(task: Any, text: str, no_match: bool = False) -> dict[str, Any]:
    if task.facts.get("hazard"):
        return plumbing_next(task, text, no_match)  # reuse hazard wrap
    ptype = task.facts.get("problem_type")
    if ptype == "wiring" or re.search(r"\binstall|\brewire|\bconsumer\s+unit\b", text, re.I):
        task.facts["needs_professional"] = True
        task.facts["diy_safe"] = False
        return _wrap_provider(
            task,
            "I will not guide you through live wiring or consumer-unit work. A licensed electrician should handle that.",
            no_match,
        )
    if not task.facts.get("breaker_checked"):
        q = (
            f"{_intro(task)} Before involving an electrician, a common cause is a tripped breaker or an unplugged appliance — "
            "not a wiring fault. Have you checked the consumer unit for a switch that has flipped, and that the appliance is plugged in?"
        )
        return {"reply": _ask(task, "breaker_checked", q), "should_dispatch": False}
    if task.facts.get("breaker_checked") == "no" and not task.facts.get("diy_offered"):
        return {
            "reply": _diy(
                task,
                "If you can do so safely, look at the consumer unit and reset a clearly tripped breaker once. Do not hold a breaker that immediately trips again, and do not open the cover or touch bare wires.",
                "A single trip often just needs a reset; repeated trips mean a fault that needs an electrician.",
            ),
            "should_dispatch": False,
        }
    task.facts["needs_professional"] = True
    return _wrap_provider(task, "If power is still out after a safe reset, that is beyond remote DIY.", no_match)


def appliance_next(task: Any, text: str, no_match: bool = False) -> dict[str, Any]:
    if not task.facts.get("power_checked"):
        q = (
            f"{_intro(task)} Many faults are just power or a simple reset. Is the appliance plugged in, and do other sockets on that wall work?"
        )
        return {"reply": _ask(task, "power_checked", q), "should_dispatch": False}
    if task.facts.get("power_checked") == "no" and not task.facts.get("diy_offered"):
        return {
            "reply": _diy(
                task,
                "Plug it into a known-working socket if you can do so without forcing damaged leads, and try the appliance's reset or power cycle if the manual has one.",
                "Loose plugs and tripped supply are common. Do not open sealed cooling or heating systems.",
            ),
            "should_dispatch": False,
        }
    ptype = task.facts.get("problem_type")
    if ptype == "not_cooling" and not task.facts.get("vents_checked"):
        q = "Are the fridge vents inside blocked with food, and has the door been closing firmly?"
        return {"reply": _ask(task, "vents_checked", q), "should_dispatch": False}
    task.facts["needs_professional"] = True
    return _wrap_provider(task, "If power and basic checks did not help, a technician should inspect it. I will not ask you to open sealed refrigerant or heating parts.", no_match)


def cleaning_next(task: Any, text: str, no_match: bool = False) -> dict[str, Any]:
    if not task.facts.get("stain_type"):
        q = f"{_intro(task)} What is stained, and what caused it if you know — oil, rust, paint, mud, or something else?"
        return {"reply": _ask(task, "stain_type", q), "should_dispatch": False}
    stain = str(task.facts.get("stain_type") or "").lower()
    if not task.facts.get("diy_offered") and not re.search(r"paint|chemical|unknown|large|whole\s+house", stain):
        return {
            "reply": _diy(
                task,
                "Blot (do not rub) with clean water first. For ordinary food or mud on washable fabric, a little washing-up liquid on a damp cloth is usually enough.",
                "Do not mix bleach with ammonia or other drain/toilet chemicals. Large, set-in, or unknown chemical stains need specialist equipment.",
            ),
            "should_dispatch": False,
        }
    task.facts["needs_professional"] = True
    return _wrap_provider(task, "That looks like a job for a cleaner with the right equipment rather than household products.", no_match)


def _water_heater_next(task: Any, text: str, no_match: bool = False) -> dict[str, Any]:
    low = (text or "").lower()
    ptype = task.facts.get("problem_type") or ""
    # Safety first
    if ptype == "water_heater_safety" or task.facts.get("hazard") == "water_heater_safety":
        return _wrap_provider(task, "If you see sparks, smell gas, feel a shock or notice a burning smell, stop using the heater, move away from the hazard and call emergency help or a qualified professional. Do not open the unit or touch wiring.", no_match)
    if re.search(r"spark|shock|burning\s+smell|gas\s+smell|smell\s+gas", low):
        task.facts["hazard"] = "water_heater_safety"
        return _wrap_provider(task, "If you see sparks, smell gas, feel a shock or notice a burning smell, stop using the heater, move away from the hazard and call emergency help or a qualified professional. Do not open the unit or touch wiring.", no_match)
    # Leak
    if ptype == "water_heater_leak" or re.search(r"leak|drip|water\s+on\s+the\s+floor", low):
        if not task.facts.get("leak_location"):
            q = "Where is the water leaking — from the tank itself, the pipes/connections, or the pressure valve?"
            return {"reply": _ask(task, "leak_location", q), "should_dispatch": False}
        task.facts["needs_professional"] = True
        return _wrap_provider(task, "A leaking water heater can worsen quickly. If you can safely reach an isolation valve, close it, but do not open the unit.", no_match)
    # Core diagnostic: cold vs runs-out-quickly
    if ptype in ("water_heater_not_heating", "water_heater_no_hot_water") or re.search(r"not\s+heating|no\s+hot\s+water|not\s+getting\s+hot", low):
        if not task.facts.get("heater_symptom_detail"):
            q = "I can help with that. Is your water heater completely cold, or does it heat the water but run out of hot water quickly?"
            return {"reply": _ask(task, "heater_symptom_detail", q), "should_dispatch": False}
        detail = str(task.facts.get("heater_symptom_detail") or "").lower()
        if "completely cold" in detail or detail.strip() == "completely cold" or "cold" in detail and "runs out" not in detail:
            if not task.facts.get("heater_type"):
                q = "Is it an electric, gas, solar or instantaneous heater, and do you see any warning lights, error codes or unusual noises?"
                return {"reply": _ask(task, "heater_type", q), "should_dispatch": False}
        elif "runs out" in detail or "run out" in detail or "quickly" in detail:
            if not task.facts.get("heater_usage_pattern"):
                q = "Does it run out every time, or only when several people use hot water in quick succession? What type of heater is it?"
                return {"reply": _ask(task, "heater_usage_pattern", q), "should_dispatch": False}
        task.facts["needs_professional"] = True
        return _wrap_provider(task, "", no_match)
    # Fallback for other water-heater mentions
    if not task.facts.get("heater_symptom_detail"):
        q = "I can help with that. Is your water heater completely cold, or does it heat the water but run out of hot water quickly?"
        return {"reply": _ask(task, "heater_symptom_detail", q), "should_dispatch": False}
    return _wrap_provider(task, "", no_match)

def generic_trade_next(task: Any, text: str, no_match: bool = False) -> dict[str, Any]:
    svc = (task.requested_service or "professional").strip()
    # Water-heater routed above before generic
    if task.facts.get("trade_family") == "water_heater" or (task.facts.get("problem_type") or "").startswith("water_heater"):
        return _water_heater_next(task, text, no_match)
    if svc.lower() in ("painting", "painter"):
        if not task.facts.get("property_type"):
            q = "Is this for a house, office or commercial building?"
            return {"reply": _ask(task, "property_type", q), "should_dispatch": False}
        # fall through to dispatch once we have property_type + location
    if not task.facts.get("issue_description") and not task.facts.get("problem_type"):
        # If service intent was recognised but problem not yet classified (e.g. sink leak, AC, roof), use specific question, not generic echo
        low_svc = svc.lower()
        if "plumb" in low_svc or "sink" in low_svc or "leak" in (task.facts.get("issue_description") or "").lower():
            q = "Where is the leak — under the sink, from a pipe joint, or from the wall/floor?"
            return {"reply": _ask(task, "leak_location", q), "should_dispatch": False}
        intro = _intro(task)
        prefix = f"{intro} " if intro else ""
        q = f"{prefix}What exactly is going wrong, in your own words? That helps me tell whether a simple check will do or whether {svc} work is needed."
        return {"reply": _ask(task, "issue_description", q), "should_dispatch": False}
    if task.facts.get("wants_advice") and not _professional_needed(task) and not task.facts.get("asked_urgency"):
        task.facts["asked_urgency"] = True
        q = "Is anyone at risk, or is anything getting worse quickly? I only recommend a paid visit when it is beyond a safe check from here."
        return {"reply": _ask(task, "urgency_note", q), "should_dispatch": False}
    if _professional_needed(task) or task.facts.get("wants_provider") or task.facts.get("issue_description"):
        if not _safe_diy_available(task) or task.facts.get("wants_provider") or _professional_needed(task):
            return _wrap_provider(task, "This is the sort of work a qualified person should handle rather than a remote guess.", no_match)
    return {"reply": None, "should_dispatch": False}


def _wrap_provider(task: Any, extra: str, no_match: bool) -> dict[str, Any]:
    loc = (task.location or "").strip()
    svc = (task.requested_service or "professional").strip()
    label = task.facts.get("problem_label") or task.facts.get("problem_summary") or svc
    skill = task.facts.get("required_skill") or f"{svc} familiar with {label}"
    task.facts["needs_professional"] = True
    task.facts["required_skill"] = skill
    _refresh_matching_brief(task)
    bits = [extra.strip()] if extra and extra.strip() else []
    if no_match:
        bits.append(
            f"I could not find a suitable {svc} listed around {loc or 'that area'} right now. "
            "I can check nearby areas. Meanwhile this request stays open — you do not need to repeat it."
        )
        if not task.facts.get("problem_type") or task.facts.get("wants_advice"):
            bits.append("If you describe the symptom a bit more, I can still talk you through safe checks.")
        task.facts["pending_prompt"] = "nearby"
        return {"reply": " ".join(b for b in bits if b), "should_dispatch": False, "pending_prompt": "nearby"}
    if loc:
        bits.append(f"When you are ready I can look for a {skill} around {loc}.")
        task.facts["pending_prompt"] = "want_provider"
        should = bool(task.facts.get("wants_provider") or task.facts.get("hazard") or _professional_needed(task))
        # Search once we know a professional is required and have location — unless still in pure advice mode without failure
        if task.facts.get("wants_advice") and not task.facts.get("diy_exhausted") and not task.facts.get("hazard") and not task.facts.get("wants_provider"):
            should = False
            bits.append("Would you like me to find someone, or try a safe check first?")
        return {"reply": " ".join(b for b in bits if b), "should_dispatch": should, "pending_prompt": task.facts["pending_prompt"]}
    bits.append("Which town or neighbourhood should I search in?")
    return {"reply": " ".join(b for b in bits if b), "should_dispatch": False}


def next_consultant_action(task: Any, text: str = "", last_assistant: str = "", no_match: bool = False) -> dict[str, Any]:
    """Return {reply, should_dispatch, pending_prompt} for a service-request consult task."""
    if task is None:
        return {"reply": None, "should_dispatch": False}
    domain = (task.domain or "").lower()
    svc = (task.requested_service or "").lower()
    family = str(task.facts.get("trade_family") or "")

    # After DIY resolved — close loop without dispatch
    if task.facts.get("diy_result") == "resolved":
        msg = "Glad that helped. Your original request is still here if it comes back or you later want a professional."
        task.facts["pending_prompt"] = ""
        return {"reply": msg, "should_dispatch": False}

    if task.facts.get("trade_family") == "water_heater" or (task.facts.get("problem_type") or "").startswith("water_heater"):
        return _water_heater_next(task, text, no_match)
    if domain == "plumbing" or "plumb" in svc or "toilet" in svc or "sink" in svc:
        return plumbing_next(task, text, no_match)
    if domain in ("hvac", "water_heater"):
        # HVAC / water-heater explicit domains
        if domain == "water_heater":
            return _water_heater_next(task, text, no_match)
        # hvac -> treat as appliance-like cooling diagnostic
        family = "appliances"
    if domain == "electrical" or "electric" in svc:
        return electrical_next(task, text, no_match)
    if family == "appliances" or re.search(r"fridge|appliance|washer|cooker|oven|ac\b|air\s*con", svc):
        return appliance_next(task, text, no_match)
    if family == "cleaning" or "clean" in svc:
        return cleaning_next(task, text, no_match)
    # Pest / roofing — specific acknowledge before generic fallback
    if domain in ("pest_control",) or "pest" in svc:
        if not task.facts.get("pest_detail"):
            q = "Where are the pests — which rooms or areas — and how widespread does it look?"
            return {"reply": _ask(task, "pest_detail", q), "should_dispatch": False}
    if domain in ("roofing",):
        if not task.facts.get("roof_leak_detail"):
            q = "Where does the water show — ceiling stain, active dripping, or wall damp? When did it start?"
            return {"reply": _ask(task, "roof_leak_detail", q), "should_dispatch": False}

    # Other service categories: light diagnosis then existing matching
    return generic_trade_next(task, text, no_match)


def should_defer_to_legacy_guide(task: Any) -> bool:
    if task is None:
        return True
    if task.intent in ("product_request", "consultation") and task.domain in ("farming", "product", "general_consult"):
        return True
    if task.domain in ("farming", "legal", "product", "venue"):
        return True
    if task.intent == "product_request":
        return True
    return False


def no_match_reply(task: Any) -> str:
    loc = (task.location or "").strip() if task else ""
    svc = (task.requested_service or "professional").strip() if task else "professional"
    label = ""
    if task:
        label = task.facts.get("problem_label") or task.facts.get("problem_summary") or ""
        task.facts["pending_prompt"] = "nearby"
        task.facts["referral_state"] = "no_match"
        task.referral_state = "no_match"
    what = label or svc
    loc_bit = loc or "that area"
    extra = ""
    if task and not should_defer_to_legacy_guide(task):
        action = next_consultant_action(task, text="", no_match=False)
        follow = (action.get("reply") or "").strip()
        # Avoid nested no-match; use diagnostic follow-up only
        if follow and "could not find" not in follow.lower() and "couldn't find" not in follow.lower():
            extra = " " + follow
        else:
            extra = " Meanwhile, tell me the main symptom and I will talk you through safe checks without you repeating the original request."
    return (
        f"I couldn't find a suitable {svc} in {loc_bit} right now. I can check nearby areas. "
        f"Meanwhile I can still help with the {what}.{extra}"
    )
