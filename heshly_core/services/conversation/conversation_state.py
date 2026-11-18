"""
Conversation State Reconstruction — authoritative memory for AI Receptionist.

Builds structured state from conversation history + current message.
Never invents; tracks what customer actually provided.
"""
from __future__ import annotations
import re
from datetime import datetime, timedelta, date
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


# --- Time normalization helpers ---
_TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.I)
# finds "6 am", "6am", "2:30 pm", "14:00" (24h with colon)
_TIME_24_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")


def _normalize_one_time(text: str) -> str | None:
    """Convert a matched time to HH:MM 24h."""
    m = _TIME_RE.search(text)
    if m:
        h = int(m.group(1))
        mins = int(m.group(2) or 0)
        ap = m.group(3).lower()
        if ap == "pm" and h != 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        return f"{h:02d}:{mins:02d}"
    # 24h fallback
    m2 = _TIME_24_RE.search(text)
    if m2:
        h, mins = int(m2.group(1)), int(m2.group(2))
        if 0 <= h <= 23 and 0 <= mins <= 59:
            return f"{h:02d}:{mins:02d}"
    return None


def extract_candidate_times(text: str) -> list[str]:
    """Extract all candidate times from text preserving order, deduped."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _TIME_RE.finditer(text or ""):
        h = int(m.group(1))
        mins = int(m.group(2) or 0)
        ap = m.group(3).lower()
        if ap == "pm" and h != 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        norm = f"{h:02d}:{mins:02d}"
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    # Also capture 24h times not caught (e.g., 14:00) but avoid double-counting
    for m in _TIME_24_RE.finditer(text or ""):
        # skip if already inside an am/pm match span
        span = m.span()
        covered = any(s <= span[0] and span[1] <= e for s, e in [mm.span() for mm in _TIME_RE.finditer(text or "")])
        if covered:
            continue
        h, mins = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mins <= 59:
            norm = f"{h:02d}:{mins:02d}"
            if norm not in seen:
                seen.add(norm)
                out.append(norm)
    return out


def _extract_date(text: str, tz: str = "Africa/Nairobi", now: datetime | None = None) -> str | None:
    """Resolve natural-language date to YYYY-MM-DD using tenant timezone."""
    low = (text or "").lower()
    # handle typos like tommorow
    normalized_low = low.replace("tommorow", "tomorrow").replace("tomorow", "tomorrow").replace("tomoroww", "tomorrow")
    if ZoneInfo is not None:
        try:
            tzinfo = ZoneInfo(tz)
        except Exception:
            tzinfo = None
    else:
        tzinfo = None
    base = now or datetime.now(tzinfo) if tzinfo else datetime.now()
    # normalize to date
    base_date = base.date()
    if "today" in normalized_low:
        return base_date.isoformat()
    if "tomorrow" in normalized_low:
        return (base_date + timedelta(days=1)).isoformat()
    # day of week
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for idx, dname in enumerate(days):
        if dname in low:
            # "next friday" vs "this friday" / bare "friday"
            is_next = "next" in low
            cur_wd = base_date.weekday()
            delta = (idx - cur_wd) % 7
            if delta == 0:
                delta = 7
            if is_next and delta < 7:
                # next friday when today is friday-like? keep as delta; if "next" explicitly, ensure minimum 7 if same week logic already 7
                pass
            target = base_date + timedelta(days=delta)
            return target.isoformat()
    # explicit YYYY-MM-DD
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text or "")
    if m:
        return m.group(1)
    # DD/MM/YYYY or MM/DD
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b", text or "")
    if m:
        # ambiguous: treat as DD/MM vs MM/DD not reliable; prefer not to invent — return None unless confident
        return None
    return None


def _extract_service(text: str, known_services: list[str] | None = None) -> str | None:
    low = (text or "").lower()
    candidates = known_services or []
    # sort longest first to prefer multi-word
    for svc in sorted(candidates, key=len, reverse=True):
        if svc.lower() in low:
            return svc  # preserve canonical case
    # fallback patterns
    patterns = {
        "dental cleaning": ["dental cleaning", "teeth cleaning", "tooth cleaning", "tooth wash", "cleaning"],
        "blood work": ["blood work", "bloodwork", "lab", "blood test"],
        "consultation": ["consultation", "consult"],
        "checkup": ["checkup", "check up", "check-up"],
        "massage": ["massage"],
    }
    for canonical, aliases in patterns.items():
        for a in aliases:
            if a in low:
                # map to known service if close, else canonical
                if candidates:
                    # try exact known match
                    for ks in candidates:
                        if ks.lower() == canonical:
                            return ks
                        if a in ks.lower():
                            return ks
                return canonical.title() if canonical != "blood work" else "Blood Work"
    return None


def build_conversation_state(
    turns: list[dict[str, Any]],
    current_message: str,
    business_knowledge: dict[str, Any] | None = None,
    timezone: str = "Africa/Nairobi",
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Reconstruct authoritative state from history + current message.
    Never invents values not in turns/current_message/knowledge.
    """
    known_services: list[str] = []
    if business_knowledge:
        svcs = business_knowledge.get("services") or []
        for s in svcs:
            name = s.get("name") if isinstance(s, dict) else getattr(s, "name", None)
            if name:
                known_services.append(str(name))

    # Walk history in order to accumulate authoritative values (last non-empty wins, times accumulate)
    service: str | None = None
    date: str | None = None
    candidate_times: list[str] = []
    selected_time: str | None = None

    # Helper to process a message text
    def ingest(text: str):
        nonlocal service, date, candidate_times
        svc = _extract_service(text, known_services)
        if svc:
            service = svc
        d = _extract_date(text, timezone, now)
        if d:
            date = d
        cands = extract_candidate_times(text)
        for c in cands:
            if c not in candidate_times:
                candidate_times.append(c)

    # History turns are ordered; last user/assistant messages hold prior context
    for turn in turns or []:
        msg = turn.get("message") if isinstance(turn, dict) else ""
        if isinstance(msg, str) and msg.strip():
            # only ingest user messages for authoritative customer facts? But keep assistant history for service inference
            # Still process all to recover prior extracted intent; but prefer user-provided facts
            ingest(msg)

    # Current message last (authoritative, may add new candidates)
    ingest(current_message or "")

    # If customer says "maybe 6 am or 2pm" then later "based on the times i gave you" without times, we preserve earlier candidates
    # No invention: if no date but history had tomorrow, we keep it; if no candidates but history had them, keep.

    # Detect booking vs availability vs greeting intent hints for guidance
    # Returned as hints, LLM still classifies but state guides hallucination guard.

    return {
        "service": service,
        "date": date,
        "candidate_times": candidate_times,
        "selected_time": selected_time,
        "known_services": known_services,
        "timezone": timezone,
    }


def hallucination_guard(
    proposed_service: str | None,
    proposed_time: str | None,
    proposed_date: str | None,
    state: dict[str, Any],
    raw_history_text: str = "",
    business_knowledge: dict[str, Any] | None = None,
) -> list[str]:
    """Return list of violations; empty means no hallucination."""
    violations: list[str] = []
    # Normalize for comparison
    if proposed_service:
        known = [s.lower() for s in (state.get("known_services") or [])] + [state.get("service","").lower()]
        # check if proposed service appears anywhere in history or known services
        history_low = raw_history_text.lower()
        if proposed_service.lower() not in history_low and proposed_service.lower() not in known:
            # also check business knowledge
            violations.append(f"service '{proposed_service}' not in conversation or business knowledge")
    if proposed_time:
        # require time to be in candidate_times or history text or explicitly "9:20" must be rejected if not in candidates
        cands = state.get("candidate_times") or []
        hist_has_time = proposed_time.lower() in raw_history_text.lower() or any(proposed_time in c for c in cands)
        # also allow normalized HH:MM match
        norm = _normalize_one_time(proposed_time) or proposed_time
        if norm not in cands and norm.lower() not in raw_history_text.lower():
            # allow if history contains same hour different minute formatting? strict for now
            violations.append(f"time '{proposed_time}' not in conversation candidate_times")
    if proposed_date:
        if proposed_date != state.get("date") and proposed_date.lower() not in raw_history_text.lower():
            violations.append(f"date '{proposed_date}' not in conversation")
    return violations
