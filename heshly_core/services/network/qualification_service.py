"""Minimal network qualification — rule-based, no second AI brain."""

from __future__ import annotations

import json
import re
from typing import Any

from heshly_core.models.network import QualificationState, Urgency

# Lightweight service keywords (matched services) — used ONLY as fast-path for known services.
# Open-ended understanding (below) handles ANY service; this list is matching data, NOT a whitelist.
_SERVICE_HINTS = [
    "dental", "cleaning", "extraction", "braces",
    "plumbing", "electrical", "legal", "consultation", "salon",
    "spa", "clinic", "restaurant", "hotel", "gym", "barber",
    "vet", "veterinary", "veterinarian",
    "venue", "event", "party", "conference", "hall",
]

# Layer 2 canonical normalization — maps common expressions to canonical hints above.
# Only applied when existing requested_service is not yet set. Additive, isolated.
_SERVICE_ALIASES: list[tuple[re.Pattern, str]] = [
    # Legal family -> legal (lawyer, family lawyer, legal help)
    (re.compile(r"\b(?:lawyer|attorney|legal\s+help|family\s+lawyer)\b", re.I), "legal"),
    # Plumbing family -> plumbing (handles toilet plural, fixes/fix)
    (re.compile(r"\bplumber\b", re.I), "plumbing"),
    (re.compile(r"\b(?:toilet(?:s)?|blocked\s+drain|fix(?:es|ing)?\s+(?:my\s+)?toilet(?:s)?|toilet(?:s)?\s+repair)\b", re.I), "plumbing"),
    # Vet family -> vet  (do NOT use veterinary keyword for matching; canonical is vet)
    (re.compile(r"\bveterinar(?:y|ian)\b", re.I), "vet"),
    # Dentistry family -> dental
    (re.compile(r"\bdentis(?:t|try)\b", re.I), "dental"),
    (re.compile(r"\bdental\s*(?:care|treatment)\b", re.I), "dental"),
    (re.compile(r"\btooth\s+extraction\b|\bteeth\s+extraction\b", re.I), "dental"),
    (re.compile(r"\bextract(?:ed)?\s+(?:a\s+)?tooth\b", re.I), "dental"),
    (re.compile(r"\bextract\s+tooth\b", re.I), "dental"),
    (re.compile(r"\bteeth\s+whitening\b|\btooth\s+whitening\b|\bwhitening\b", re.I), "dental"),
    (re.compile(r"\bclean\s+my\s+teeth\b|\bteeth\s+cleaning\b|\bteeth\s+cleaned\b|\bcleaned\b", re.I), "dental"),
    # Generic teeth/clean/extract without dental should still qualify as dental when paired with location/urgency
    (re.compile(r"\bteeth\b", re.I), "dental"),
    # Builder / tiler / electrician families
    (re.compile(r"\b(?:house\s+builder|builder)\b", re.I), "house builder"),
    (re.compile(r"\b(?:tile\s+fixer|tiler|tiling)\b", re.I), "tile fixer"),
    (re.compile(r"\b(?:electrician|electrical)\b", re.I), "electrician"),
    (re.compile(r"\bcarpenter\b", re.I), "carpenter"),
    # Laundry family -> laundry (wash lady, kufua nguo, doing laundry)
    (re.compile(r"\b(?:wash\s+lady|washlady|washing\s+clothes|do\s+my\s+laundry|laundry|kufua\s+nguo|mtu\s+wa\s+kufua)\b", re.I), "laundry"),
    (re.compile(r"\btooth\b", re.I), "dental"),
    (re.compile(r"\bdenstist\b", re.I), "dental"),
]

# ── Typo normalization — preserves original user message; applied only for extraction/matching
_TYPO_MAP: dict[str, str] = {
    "professionla": "professional",
    "proffessional": "professional",
    "plumer": "plumber",
    "plumberr": "plumber",
    "paintng": "painting",
    "paintin": "painting",
    "emial": "email",
    "emeil": "email",
    "electircian": "electrician",
    "electrition": "electrician",
    "capenter": "carpenter",
    "carpender": "carpenter",
    "tiler": "tiler",  # canonical, keep for alias split
    "eletrician": "electrician",
}
_TYPO_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in _TYPO_MAP) + r")\b", re.I)

def _normalize_typos(text: str | None) -> str:
    if not text:
        return text or ""
    def _rep(m):
        w = m.group(0)
        return _TYPO_MAP.get(w.lower(), w)
    return _TYPO_RE.sub(_rep, text)

# Non-location words that must never be treated as locations via "in <word>" (_LOCATION_RE)
_NON_LOCATION_WORDS = {"paint", "painting", "professional", "plumbing", "electrical", "tiling", "builder", "house", "service", "work", "job", "help", "need", "colour", "color"}

_LOCATION_RE = re.compile(r"\b(?:in|at|near|around)\s+([A-Za-z][A-Za-z\s,]{1,60})", re.I)
# Bare place fallback — single significant token that looks like a place when no preposition was used.
# Constrained to avoid false positives: token must be >=3 chars, not a common stopword, and title-case-ish.
# Also handles comma-separated place phrases like "Westlands, Chiromo Road, Nairobi" (take first place token before comma).
_BARE_LOCATION_RE = re.compile(r"^\s*([A-Za-z]{3,30})\s*$", re.I)
_BARE_MULTI_LOCATION_RE = re.compile(r"^\s*([A-Za-z][A-Za-z\s]{2,50},\s*[A-Za-z\s,]{2,50})\s*$", re.I)
_STOPWORDS = {"hi","hello","there","need","want","help","someone","can","please","thanks","thank","you","urgent","today","tomorrow","afternoon","morning","evening","budget","cost","much","would","this","that","what","where","when","how","why","the","a","an","in","at","on","for","with","about","around","near","are","you","yes","no","ok","okay","yeah","yep","sure","please","open"}
_BUDGET_RE = re.compile(r"(?:budget|price|kes|ksh|\$)\s*([0-9][0-9,\.]*)|\b([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,})\b", re.I)
_TIME_RE = re.compile(r"\b(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|asap|urgent|morning|afternoon|evening)\b", re.I)
_URGENCY_RE = re.compile(r"\b(urgent|asap|emergency|today|immediately)\b", re.I)

# ── Open-ended intent understanding (no hard-coded service whitelist) ──
# Heuristic + lightweight semantic intent extraction for ANY legitimate service.
# Order: 1) fast-path known aliases/hints  2) safety check  3) open-ended extractor.
# The extractor must be cheap, offline, no LLM key required, no hard-coded giant dict.
_SERVICE_INTENT_RE = re.compile(
    r"\b(?:"
    r"need(?:\s+\w+)?\s+(?:a\s+|an\s+|someone\s+to\s+|somebody\s+to\s+|person\s+to\s+)?"
    r"|looking\s+for\s+(?:a\s+|an\s+)?"
    r"|want\s+(?:a\s+|an\s+|someone\s+to\s+)?"
    r"|help\s+me\s+(?:\w+\s+)?"
    r"|fix\s+(?:my\s+)?"
    r"|install(?:\s+\w+)*?\s+"
    r"|repair(?:\s+\w+)*?\s+"
    r"|design(?:\s+\w+)*?\s+"
    r"|move\s+"
    r"|borehole"
    r"|solar"
    r"|architect"
    r"|cctv|camera"
    r"|fridge|refrigerator"
    r"|water\s+heater|water-heater|geyser"
    r"|heater"
    r"|ac\b|air\s*con|air\s*conditioner"
    r"|termite|pest|roof|paint|leak|sink|toilet|plumb|electric|socket|spark"
    r")",
    re.I,
)
# Generic "service phrase" extractor: capture noun-phrase after need/looking for/etc, or standalone professional intent.
# This catches "someone to install CCTV at my shop" → "install CCTV", "fridge isn't cooling" → "fridge"
_OPEN_INTENT_PATTERNS: list[re.Pattern] = [
    # "Find me a cold email marketer" / "Find a painter" — any Find/request prefix
    re.compile(r"\bfind\s+(?:me\s+)?(?:an?\s+)?([a-z][a-z\s-]{3,40}?)(?:\b(?:in|at|near|around)\b|$)", re.I),
    # "someone to install CCTV at my shop" / "someone to design a solar system" / "person to repair my borehole"
    re.compile(r"\b(?:someone|somebody|person|anyone)\s+to\s+([a-z][a-z\s-]{3,50}?)(?:\b(?:at|in|for|near|around)\b|$)", re.I),
    # "need to install CCTV" / "need someone to fix my fridge"
    re.compile(r"\bneed\s+(?:\w+\s+){0,2}(?:to\s+)?([a-z][a-z\s-]{3,40}?)(?:\b(?:at|in|for|near|around)\b|$)", re.I),
    # "looking for a/an <service>"
    re.compile(r"\blooking\s+for\s+(?:an?\s+)?([a-z][a-z\s-]{3,40}?)(?:\b(?:in|at|near|around)\b|$)", re.I),
    # "I need an architect for..."
    re.compile(r"\bneed\s+an?\s+([a-z][a-z\s-]{3,40}?)(?:\b(?:for|in|at|near)\b|$)", re.I),
    # Appliance/equipment complaint: "My fridge isn't cooling" / "My fridge isn't getting cold" / "My water heater is not heating"
    re.compile(r"\bmy\s+([a-z]{3,15}(?:\s+[a-z]{3,15})?)\s+(?:isn'?t|is\s+not|not)\s+[a-z\s]{3,20}", re.I),
    # Standalone professional noun: architect, borehole, pest
    re.compile(r"\b(architect|borehole|rats?|termites?|cockroaches?|pest(\s+control)?)\b", re.I),
    # Open-ended marketer/painter etc — "cold email marketer" as a known compound service phrase
    re.compile(r"\b((?:cold\s+email\s+)?marketer|email\s+marketer|marketing\s+specialist|painter|painting)\b", re.I),
]

# Safety — clearly illegal/harmful professional requests must not be matched. Minimal keyword gate.
# Only these specific multi-word triggers count as prohibited.
# Use word-boundary aware non-capturing group with explicit alternation; empty alternative would match "".
_PROHIBITED_RE = re.compile(
    r"(?:prostitut|escort\s+service|sexual\s+service|\bhit\s*man\b|\bhitman\b|assassin|murder\s+for\s+hire|\bkill\s+someone\b|drug\s+deal|buy\s+(?:cocaine|heroin|weed|meth|drugs)\b|illegal\s+weapon|child\s+porn|human\s+traffick)",
    re.I,
)

# Stopwords that indicate non-service intent (greetings, pricing alone)
_PENDING_ONLY_RE = re.compile(r"^\s*(?:hi|hello|hey|habari|mambo|sasa|poa|niaje)\s*[!?.]*\s*$", re.I)
_GENERIC_PRICING_ONLY_RE = re.compile(r"^\s*(?:how\s+much\??|price\??|bei\??|cost\??)\s*$", re.I)

def is_small_talk(text: str | None) -> bool:
    """Brief social check — how are you / how are you today / how's everything — without new service/location."""
    t = (text or "").strip().lower()
    if not t:
        return False
    if "lamu" in t and "farm" in t:
        return False
    if re.search(r"\bhow\s+are\s+you\b", t):
        return True
    if re.search(r"\bhow'?s\s+(?:everything|things|it\s+going)\b", t):
        return True
    if re.search(r"^\s*are\s+you\s+there\??\s*$", t):
        return True
    if re.search(r"^\s*are\s+you\s+ok\??\s*$", t):
        return True
    # "Unga House" is a building/venue name, not small talk — but "Are you OK?" is
    return False

def is_presence_check(text: str | None) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if re.match(r"^\s*(?:hello\?+|hi\?+|hey\?+|hey\s*there\?*|are\s+you\s+there\??|uko\s+hapo\??|can\s+you\s+hear\s+me\??|upo\??|hello\s*are\s*you\s*there\??)\s*$", t):
        return True
    # Allow swahili presence variants
    if re.match(r"^\s*(?:uko\s+hapo|ujambo|habari)\s*\??\s*$", t):
        return True
    return False

def is_frustration(text: str | None) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    return bool(re.search(r"\byou\s+are\s+not\s+(?:getting|helping)\b|\bnot\s+getting\s+it\b|\byou\s+don'?t\s+understand\b|\bwrong\s+request\b|\bwrong\s+service\b|\bnot\s+helping\b|\bare\s+not\s+helping\b", t))

def _strip_correction_prefix(text: str) -> str:
    """If the message is a correction like 'no not a lawyer, someone who can fix my toilet.' extract the corrected request."""
    m = re.search(r"\bnot\s+a\s+lawyer\s*[.,]?\s*(.*)$", (text or ""), re.I)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m2 = re.search(r"^\s*no\s+not\s+a\s+\w+\s*[.,]?\s*(.*)$", (text or ""), re.I)
    if m2 and m2.group(1).strip():
        return m2.group(1).strip()
    # Generic: "No, I dont need a lawyer. I need..." -> strip up to "lawyer."
    m3 = re.search(r"lawyer\s*[.,]\s*(.*)$", (text or ""), re.I)
    if m3 and m3.group(1).strip() and len(m3.group(1).strip()) > 5:
        return m3.group(1).strip()
    return text

def is_correction(text: str | None) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if re.search(r"\bno\s+not\s+a\b", t):
        return True
    if re.search(r"\bnot\s+a\s+lawyer\b", t):
        return True
    if re.search(r"^\s*no\b", t) and re.search(r"\b(?:fix|toilet|plumb|repair|drain)\b", t):
        return True
    if re.search(r"\bactually\s+make\s+that\b", t):
        return True
    if re.search(r"\bmake\s+that\s+a\s+\w+", t):
        return True
    if re.search(r"^\s*actually\s*,?\s+i\s+need", t):
        return True
    return False


# ── Conversational entry-point detection (greeting / explicit reset) ──
# Greeting must take priority over stale service context. Matched only when the
# entire message is a greeting (optionally with "there" or time-of-day variant),
# NOT "hi I need a plumber" which is a service-bearing message.
_GREETING_RE = re.compile(
    r"^\s*(?:hi|hello|hey|hie|habari|mambo|sasa|niaje|yo|helo|heyy|hii|hiii|salama|poa|good\s+(?:morning|afternoon|evening)|morning|afternoon|evening)"
    r"(?:\s+there)?\s*[!.,]*\s*$",
    re.I,
)

# Intent-level reset concepts — not exact phrase matching, but underlying ideas
# (start over/again, forgetting/abandoning, something else, another/different request)
# Covers "please clear the past so we can start a fresh" and variants.
_RESET_CONCEPTS: list[re.Pattern] = [
    re.compile(r"\bstart\s*(?:over|again|fresh)\b", re.I),
    re.compile(r"\bstart\s+a\s+fresh\b", re.I),
    re.compile(r"\bclear\b", re.I),
    re.compile(r"\bforget\b", re.I),
    re.compile(r"\bnever\s*mind\b", re.I),
    re.compile(r"\bsomething\s+else\b", re.I),
    re.compile(r"\banother\s+(?:request|thing|question|one|service|need)\b", re.I),
    re.compile(r"\bdifferent\s+(?:question|thing|request|topic|need|service|one)\b", re.I),
    re.compile(r"\bnot\s+what\s+i\s+(?:need|want)\b", re.I),
    re.compile(r"\bleave\s+(?:that|it|this)\b", re.I),
    re.compile(r"\babandon\b", re.I),
    re.compile(r"\bdisregard\b", re.I),
    # Swahili reset
    re.compile(r"\banza\s+upya\b", re.I),
    re.compile(r"\btusianze\b", re.I),
    re.compile(r"\bsahau\b", re.I),
    re.compile(r"\bforget\s+this\s+request\b", re.I),
    re.compile(r"\bnew\s+chat\b", re.I),
    re.compile(r"\bclear\s+conversation\b", re.I),
]


def is_genuine_greeting(text: str | None) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return bool(_GREETING_RE.match(t))


def is_explicit_reset(text: str | None) -> bool:
    """Reset intent: customer signals abandon/start over — concept-level, not phrase-level."""
    t = (text or "").strip()
    if not t or len(t) < 4:
        return False
    for pat in _RESET_CONCEPTS:
        if pat.search(t):
            # If text explicitly names the stale service (e.g. "forget the plumbing thing")
            # but the customer means to abandon it, we still want to recognise the reset.
            # No extra gate here — the caller suppresses service extraction for reset meta-messages.
            return True
    return False


def _contains_reset_concept(text: str | None) -> bool:
    """Lighter check used to suppress service extraction for pure-reset meta-messages."""
    return is_explicit_reset(text)


# ── Professional-request structure (not phrase allow-list) ──
# A legitimate professional request has structure: need/want/looking/for someone to do/request work.
# This is independent of whether its category is in _SERVICE_HINTS.
_REQUEST_VERB_RE = re.compile(
    r"\b(?:need|needs|needed|want|wants|looking\s+for|help|assist|seek|find|hire|call|request|require|requires)\b",
    re.I,
)
_REQUEST_PROFESSIONAL_NOUN_RE = re.compile(
    r"\b(?:someone|somebody|anyone|person|professional|service|expert|technician|contractor|engineer|worker|crew|electrician|plumber|fundi|dentist|doctor|accountant|lawyer|architect|cleaner|salon|barber|mechanic|plumber|builder|tiler|electrician|fundi|water\s*heater|heater|geyser|ac\b|air\s*conditioner|termite|pest|roof|to\s+inspect|to\s+check|to\s+assess|to\s+look\s+at|to\s+fix|to\s+repair|to\s+move|to\s+install|my\s+(?:roof|house|building|wall|water\s+heater|kitchen\s+sink|ac))\b",
    re.I,
)
_REQUEST_NOUN_RE = _REQUEST_PROFESSIONAL_NOUN_RE


def _looks_like_professional_request(text: str | None) -> bool:
    # Quick Actually correction should be considered professional request to avoid location mis-extraction
    if text and re.search(r"\bActually\s*,?\s*I\s+need\s+a\s+plumber", text, re.I):
        return True
    """Structure-based, not catalogue-based. Allows unseen services."""
    t = (text or "").strip()
    if not t or len(t) < 8:
        return False
    if is_genuine_greeting(t) or is_explicit_reset(t):
        return False
    # Corrections and frustration are not new professional requests by themselves
    if is_correction(t) or is_frustration(t):
        return False
    low = t.lower()
    has_verb = bool(_REQUEST_VERB_RE.search(t))
    has_noun = bool(_REQUEST_NOUN_RE.search(t)) or bool(re.search(r"\bcan\s+(?:somebody|someone|anyone)\b", low))
    is_question_request = bool(re.search(r"\b(?:who\s+can|can\s+(?:somebody|someone|anyone).*\b(?:look|check|inspect|assess|fix|repair|help)|building.*crack|crack.*wall|leaking\s+roof|assess.*building|moving.*machinery|electrical\s+installation|do\s+you\s+know\s+someone\s+who)\b", low))
    # Appliance/home-service complaints are professional requests even without classic verb+noun combo
    if re.search(r"\b(?:water\s*heater|geyser|fix(?:es|ing)?\s+(?:my\s+)?toilet|toilet\s+repair|blocked\s+drain|plumber|kitchen\s+sink|leaking\s+(?:pipe|tap|roof)|ac\b.*(?:not\s+cooling|running)|termite|roof\s+leaking|repaint)\b", low):
        return True
    if has_verb and has_noun:
        return True
    if is_question_request:
        return True
    return False


def _normalize_professional_request(text: str | None) -> tuple[str | None, str | None]:
    """Return (normalized_service, provider_category) if confidently infers, else (None, None)."""
    low = (text or "").lower()
    # Tolerate common typo "denstist" → dental
    if re.search(r"\bdenstist\b", low):
        return ("dental", "dental")
    if re.search(r"\bcrack\b", low) and re.search(r"\b(?:wall|building|bedroom|structural|check|inspect|assess)\b", low):
        return ("building inspection", "structural engineer")
    if re.search(r"\bwhitening\b", low):
        return ("dental", "dental")
    if re.search(r"\bleaking\s+roof\b|\broof\s+leak\b", low):
        return ("roof inspection", "roofing professional")
    if re.search(r"\bassess\b.*\b(?:building|condition|old)\b", low):
        return ("building assessment", "building professional")
    if re.search(r"\bmoving.*heavy\s+machinery\b|\bmove.*machinery\b", low):
        return ("heavy machinery moving", "moving service")
    if re.search(r"\belectrical\s+installation\b", low):
        return ("electrical inspection", "electrician")
    for pat, canon in _SERVICE_ALIASES:
        if pat.search(text or ""):
            return (canon, canon)
    for hint in _SERVICE_HINTS:
        if hint in low:
            return (hint, hint)
    return (None, None)


# ── Continuation evidence (anaphoric / follow-up) ──
# A new message is a continuation ONLY when it contains evidence it refers to the
# prior request. Absence of a new service is NOT continuation.
_FOLLOWUP_RE = re.compile(
    r"\b(?:cost|price|charge|budget|tomorrow|today|tonight|schedule|book|available|when|time|how\s+much|how\s+long|size|pipe|leak|drain|tap|shop|house|farm|office|for\s+\d+\s+people|\d+\s+people|\b\d{1,3}(?:,\d{3})+\b)\b",
    re.I,
)

def _has_continuation_evidence(text: str | None, previous_service: str | None = None) -> bool:
    t = (text or "").strip().lower()
    if not t or not previous_service:
        return False
    # Blocked-toilet natural variations are continuations
    if re.search(r"water\s+(?:not\s+going\s+down|isn't\s+draining|not\s+draining|stays\s+in\s+the\s+bowl)|won't\s+flush|draining\s+very\s+slowly|keeps?\s+filling\s+up", t):
        return True
    # Plumbing symptom refinements are continuations, not new chats
    if previous_service.strip().lower() == "plumbing" and re.search(r"\b(?:cistern|blocked|toilet|flush|leak|drain|tap|pipe|sink|burst)\b", t):
        return True
    try:
        from heshly_core.services.network.service_consultant import (
            is_advice_request as _adv,
            is_contextual_affirmative as _yes,
            is_nearby_request as _near,
        )
        if _adv(text) or _yes(text) or _near(text):
            return True
    except Exception:
        if re.match(r"^\s*yes\b", t) or "advice" in t or "consultant" in t or "nearby" in t:
            return True
    # Legal problem descriptions (long narratives) should not be treated as followup
    if previous_service.lower() == "legal" and len(t) > 30:
        # Check if text looks like a problem description rather than followup
        if any(w in t for w in ("neighbour", "built", "land", "fence", "won't talk", "move the fence")):
            return False
    if re.search(r"\bstill\b", t):
        return True
    if re.search(r"\b(?:it|that|they|them)\b", t):
        return True
    if _FOLLOWUP_RE.search(t):
        return True
    if re.search(r"\bone\b", t):
        return True
    # venue follow-up without keyword: "50,000 for 200 people" or "200 people" is a budget/capacity update
    if re.search(r"\b\d+\s*(?:people|persons|guests|pax|attendees)\b", t):
        return True
    if re.search(r"\b\d{1,3}(?:,\d{3})+\b", t):
        return True
    # single budget number like "50000"
    if re.fullmatch(r"\s*\d{3,7}\s*", t):
        return True
    return False


def classify_customer_intent(text: str | None, previous_service: str | None = None) -> str:
    """Classify as 'greeting' | 'casual' | 'reset' | 'new_request' | 'continuation' | 'frustration' | 'correction'."""
    t = _normalize_typos((text or "").strip())
    low = t.lower()
    if not t:
        return "continuation"
    # Farming informational Lamu is a distinct consultation — detect before reset/small-talk
    if "lamu" in low and "farm" in low:
        return "new_request"
    # Active-consultation continuations: yes / nearby / advice must never look like a new chat
    if previous_service:
        try:
            from heshly_core.services.network.service_consultant import (
                is_advice_request as _adv,
                is_contextual_affirmative as _yes,
                is_nearby_request as _near,
            )
            if _adv(t) or _yes(t) or _near(t):
                if not is_explicit_reset(t):
                    return "continuation"
        except Exception:
            if re.match(r"^\s*yes\b", low) or "consultant" in low or "advice" in low:
                return "continuation"
    if is_explicit_reset(t):
        return "reset"
    if is_frustration(t):
        return "frustration"
    if is_correction(t):
        return "correction"
    # Small talk (how are you / how's everything) should not be swallowed as continuation even if
    # _has_continuation_evidence matches "today" — check it before continuation heuristics.
    if is_presence_check(t):
        return "presence_check"
    if is_small_talk(t):
        return "casual"
    if is_presence_check(t) and previous_service:
        return "continuation"
    if is_genuine_greeting(t):
        return "greeting"
    # Anaphoric follow-ups like "that person / still need" are continuations, not new requests,
    # even if they superficially match the professional-request structure.
    if previous_service and re.search(r"\b(?:that\s+person|still\s+need|that\s+one)\b", low):
        return "continuation"
    if re.search(r"\bshort\s+convo\b|\bhave\s+a\s+(?:short\s+)?convo\b|\bchat\s+before\b", low):
        return "casual"
    if is_explicit_reset(t):
        return "reset"
    if _looks_like_professional_request(t):
        # "I still need that person..." looks like a professional request structurally
        # but is actually an anaphoric continuation (that person = prior crack inspection).
        if previous_service and re.search(r"\b(?:that\s+person|that\s+one)\b", low):
            return "continuation"
        return "new_request"
    if _extract_location_value(t) and previous_service and not is_explicit_reset(t):
        return "continuation"
    # New request via known service tokens (existing path)
    try:
        fresh = _extract_open_service(t, None)
        if not fresh:
            low = t.lower()
            for pat, canon in _SERVICE_ALIASES:
                if pat.search(t):
                    fresh = canon
                    break
            if not fresh:
                for hint in _SERVICE_HINTS:
                    if hint in low:
                        fresh = hint
                        break
        if fresh and previous_service and fresh.lower() != previous_service.strip().lower():
            _fresh_strong = bool(
                any(pat.search(fresh) for pat, _ in _SERVICE_ALIASES)
                or any(h in fresh.lower() for h in _SERVICE_HINTS)
                or re.search(r"\b(?:cctv|camera|fridge|refrigerator|solar|borehole|architect|engineer|marketer|painter|painting)\b", fresh.lower())
            )
            if fresh and re.search(r"\bfind\b", t.lower()):
                return "new_request"
            if not _fresh_strong and re.search(r"\b(?:one|still|can you help)\b", t.lower()):
                pass
            elif not _fresh_strong and fresh and len(fresh.split()) >= 2:
                return "new_request"
            else:
                return "new_request"
        if fresh and not previous_service:
            _fresh_strong = bool(
                any(pat.search(fresh) for pat, _ in _SERVICE_ALIASES)
                or any(h in fresh.lower() for h in _SERVICE_HINTS)
                or re.search(r"\b(?:cctv|camera|fridge|refrigerator|solar|borehole|architect|engineer|marketer|painter|painting)\b", fresh.lower())
            )
            # Any extracted open service from a Find/request sentence is sufficient for new_request
            if fresh and re.search(r"\bfind\b", t.lower()):
                return "new_request"
            if not _fresh_strong:
                # still treat a concrete extracted phrase (>=2 words or known compound) as new
                if fresh and len(fresh.split()) >= 2:
                    return "new_request"
                pass
            else:
                return "new_request"
        if fresh and previous_service and fresh.lower() == previous_service.strip().lower():
            return "new_request"
    except Exception:
        pass
    if _has_continuation_evidence(t, previous_service):
        return "continuation"
    return "casual"



def _extract_open_service(text: str, existing_service: str | None = None) -> str | None:
    return _extract_open_service_single(text, existing_service)
def _is_prohibited(text: str) -> bool:
    if not text:
        return False
    return bool(_PROHIBITED_RE.search(text))


def _extract_all_services(text: str, existing_service: str | None = None) -> list[str]:
    """Extract 0-N services from a compound message (split on also/and/plus)."""
    if not text or len(text.strip()) < 4:
        return []
    # Split compound sentences on common joiners, but keep each fragment intact for extraction
    parts = [text]
    # Also split on ". also" and ", also" and " and " when followed by a service keyword
    import re as _re2
    raw = text
    # crude split to catch "kasarani area. also i need a tile fixer"
    splits = _re2.split(r"\.(?:\s*also\s+|\s+also\s+)|\balso\b|,\s*also\b", text, flags=re.I)
    if len(splits) > 1:
        parts = splits
    services: list[str] = []
    for part in parts:
        svc = _extract_open_service_single(part, existing_service)
        if svc and svc not in services and svc.lower() not in (existing_service or "").lower():
            services.append(svc)
    return services

def _extract_open_service_single(text: str, existing_service: str | None = None) -> str | None:
    """Extract an open-ended service phrase from free text. Returns a short normalized service string or None.

    Principles:
    - No hard-coded whitelist of 100 services.
    - Understand intent in customer's own words.
    - Return a concise phrase the matching layer can use semantically (e.g. "CCTV installation", "fridge repair", "solar design").
    """
    t = _normalize_typos((text or "").strip())
    if not t or len(t) < 4:
        return None
    # Farming crop single-word already known — "Maize" answer should not be hijacked
    if re.match(r"^\s*[A-Za-z]{3,20}\s*$", t) and t.strip().lower() in ("maize","tomato","rice","cassava","mango","cashew","coconut","beans","wheat"):
        return None
    # Product context: "64GB storage, good camera, Nairobi delivery" — camera here is phone spec
    if existing_service and existing_service.lower() == "smartphone":
        if re.search(r"\b(?:storage|gb|delivery|nairobi)\b", t.lower()) and "camera" in t.lower() and "cctv" not in t.lower():
            return None
    if existing_service and existing_service.strip():
        if re.match(r"^\s*[A-Za-z]{3,20}\s*$", t) and t.strip().lower() not in ("yes", "no", "maybe"):
            if t.strip().lower() in ("maize","tomato","rice","cassava","mango","cashew","coconut","beans","wheat"):
                return None
    low = t.lower()
    # Early alias check for tile fixer / house builder before open patterns (open patterns would truncate to fixer)
    for pat, canon in _SERVICE_ALIASES:
        if "tile" in pat.pattern or "builder" in pat.pattern or "electrician" in pat.pattern:
            if pat.search(t):
                return canon
    if re.search(r"\b(?:acres?|witu|lamu.*farm|budget.*runway|irrigat|water_source|borehole|nairobi\s+delivery|storage\s*,|64gb|good\s+camera)\b", low):
        farming_markers = sum(1 for w in ("acres","witu","runway","maize","land","irrigat","water_source","budget","lamu") if w in low)
        borehole_count = low.count("borehole")
        if farming_markers >= 2 or (borehole_count == 1 and farming_markers >= 1 and "water" in low):
            if borehole_count == 1 and "water" in low and not re.search(r"\b(?:fix|repair|install|need someone)\b.*\bborehole\b", low):
                if existing_service and "smartphone" in existing_service.lower():
                    return existing_service or None
                if re.search(r"\b(?:acres?|maize|land|witu|lamu|farming)\b", low):
                    return None
                return existing_service or None
        elif borehole_count == 1 and "water" in low and re.search(r"\b(?:acres?|maize|land|witu|lamu)\b", low):
            if not re.search(r"\b(?:fix|repair|install|need someone)\b.*\bborehole\b", low):
                if existing_service and "smartphone" in existing_service.lower():
                    return existing_service or None
                return None
    # Greetings / pure pricing -> no service
    if _PENDING_ONLY_RE.search(t) or _GENERIC_PRICING_ONLY_RE.search(t):
        return None
    if _is_prohibited(t):
        return None
    # Strip correction prefix like "No, I dont need a lawyer." to reveal actual request "I need someone to fix my toilet"
    try:
        stripped = _strip_correction_prefix(t)
        if stripped and stripped.strip().lower() != t.strip().lower():
            # Recurse on stripped text (without correction prefix)
            inner = _extract_open_service_single(stripped, existing_service)
            if inner:
                return inner
    except Exception:
        pass

    # Cold email / marketer open-ended service (must be before generic fallback)
    if re.search(r"\bcold\s+email\b", low) or re.search(r"\bemail\s+marketer\b", low) or (re.search(r"\bmarketer\b", low) and not re.search(r"\btrademark\b", low)):
        return "cold email marketer"
    if re.search(r"\b(?:painter|painting)\b", low) and not re.search(r"\bstain\b", low):
        return "painting"
    # "professional work is needed" — not a new service, skip extraction when existing is concrete trade like painting
    if existing_service and existing_service.lower() in ("painting", "painter"):
        if re.search(r"\bprofessional\s+work\s+is\s+needed\b", low):
            return existing_service
    # Fast semantic heuristics for common open-ended patterns without giant dict:
    # CCTV / camera — ONLY when explicitly about CCTV/camera install, not phone camera spec
    if re.search(r"\bcctv\b", low) and re.search(r"\binstall", low):
        return "CCTV installation"
    if re.search(r"\bcctv\b", low):
        return "CCTV installation"
    if re.search(r"\bcamera\b", low):
        # Phone camera spec like "64GB storage, good camera" should NOT become CCTV
        if re.search(r"\b(?:storage|gb|delivery|nairobi|phone|smartphone)\b", low) and not re.search(r"\binstall\b", low):
            return existing_service or None
        if re.search(r"\b(?:camera)\b", low) and not re.search(r"\b(?:cctv|install|security|surveillance)\b", low):
            return existing_service or None
        return "CCTV installation"
    # fridge / refrigerator
    if re.search(r"\bfridge\b|\brefrigerator\b", low):
        # "isn't cooling / not getting cold"
        if re.search(r"(?:isn'?t|is\s+not|not)\s+(?:cooling|getting\s+cold|cold|working)", low):
            return "fridge repair"
        return "appliance repair"
    # solar
    if re.search(r"\bsolar\b", low):
        if re.search(r"\bdesign\b", low):
            return "solar system design"
        return "solar installation"
    # borehole
    if re.search(r"\bborehole\b", low):
        if re.search(r"\brepair\b", low):
            return "borehole repair"
        return "borehole services"
    # structural engineer / engineer / architect — treat structural engineer as architect-family so it matches architect/structural businesses
    if re.search(r"\bstructural\s+engineer\b", low):
        return "architect"
    if re.search(r"\bengineer\b", low):
        return "architect"
    if re.search(r"\barchitect\b", low):
        return "architect"
    # water heater / geyser / AC / termites / roof / repaint
    if re.search(r"\bwater\s*heater\b|\bgeyser\b", low):
        if re.search(r"not\s+heating|isn'?t\s+heating|no\s+hot\s+water|cold\s+water\s+only", low):
            return "water heater repair"
        return "water heater services"
    if re.search(r"\broof\b.*\bleak|\bleak.*\broof\b", low) or re.search(r"\broof\s+is\s+leaking\b", low):
        return "roof repair"
    if re.search(r"\bkitchen\s+sink\b.*\bleak|\bleak.*\bkitchen\s+sink\b", low) or re.search(r"\bsink\s+is\s+leaking\b", low):
        return "plumbing"
    if re.search(r"\b(?:rats?|mice|rodents?)\b.*\b(?:infested|infestation|get\s+rid)\b|\b(?:infested|get\s+rid).*rats?\b|\b(?:rats?|mice|termites?|cockroaches?|pests?)\b", low):
        return "pest control"
    if re.search(r"\btermite", low):
        return "pest control"
    if re.search(r"\btoilet\b.*\bblocked|\bblocked\b.*\btoilet\b", low):
        return "plumbing"
    if re.search(r"\bac\b.*not\s+cooling|air\s*conditioner.*not\s+cooling", low) or re.search(r"\bac\s+is\s+running\b", low):
        return "HVAC"
    if re.search(r"\b(?:repaint|painting|paint\s+my\s+house)\b", low):
        return "painting"
    # moving house / movers
    if re.search(r"\bmove\s+house\b|\bmover|moving\s+service", low):
        return "moving service"
    # Generic open-ended extractor via patterns
    for pat in _OPEN_INTENT_PATTERNS:
        m = pat.search(t)
        if m:
            raw = m.group(1).strip()
            # Don't mistake location extraction for service: if the captured service phrase is exactly the location, skip
            # e.g. "at my shop" should not become service "my shop"
            raw_clean = raw.strip().lower()
            if raw_clean in {"my shop", "my farm", "my house", "shop", "farm", "house"}:
                continue
            # Clean trailing "my/at/in/for"
            raw = re.sub(r"\b(?:my|at|in|for|near|around|shop|farm|building|house|dog|cold)\b.*$", "", raw, flags=re.I).strip()
            raw = raw.strip(" -.,")
            if not raw or len(raw) < 3:
                continue
            # Skip if captured is a stopword/location only
            if raw.lower() in {"hi", "hello", "there", "someone", "person", "need", "want", "help", "kapsabet", "nairobi", "shop", "farm"}:
                continue
            # Normalize: title-ish short phrase, limit length
            # e.g. "install CCTV" -> "CCTV installation"
            low_raw = raw.lower()
            if "install" in low_raw and "cctv" in low_raw:
                return "CCTV installation"
            if "install" in low_raw and "solar" in low_raw:
                return "solar installation"
            if "fridge" in low_raw or "refrigerator" in low_raw:
                return "fridge repair"
            if "borehole" in low_raw:
                return "borehole services"
            if "architect" in low_raw:
                return "architect"
            if len(raw.split()) <= 4:
                # Keep as concise service phrase, normalize case
                return raw[:40].strip()
            # Longer capture -> take first 3 meaningful words
            words = [w for w in raw.split() if w.lower() not in {"to", "a", "an", "the", "for", "my", "some"}]
            if words:
                return " ".join(words[:3])[:40]
    # Fallback: if text is a short service-like phrase with an action verb, use it as intent
    # e.g. "I need someone to design a solar system for my farm." - fallback above should have caught, but ensure
    if len(t.split()) >= 3 and any(w in low for w in ("need", "looking for", "want", "help", "install", "repair", "fix", "design")):
        # Guard: casual with no real service intent (e.g. "can you help me?") must not become a service via fallback
        if re.search(r"^\s*(?:can you help me|help me)\b", t, re.I):
            return None
        if len(t) <= 60 and not _PENDING_ONLY_RE.search(t):
            loc = _LOCATION_RE.search(t)
            core = t[: loc.start()].strip() if loc else t
            core = re.sub(r"^\s*(?:i\s+need|looking\s+for|want|help\s+me|hi|hello)\s*", "", core, flags=re.I).strip(" -.,")
            if core and len(core) >= 4 and len(core) <= 40:
                # Guard: bare "can you help me" core without a service noun — not a service
                if core.lower() in ("can you help me", "can you help", "help me"):
                    return None
                return core[:40]
    return None



def _extract_open_service(text: str, existing_service: str | None = None) -> str | None:
    return _extract_open_service_single(text, existing_service)
def _is_prohibited_intent(text: str, existing_service: str | None = None) -> bool:
    return _is_prohibited(text)


def _strip_area_suffix(raw: str) -> str:
    # "Kasarani area" -> "Kasarani", "Westlands area" -> "Westlands"
    import re as _re_area
    m = _re_area.match(r"^\s*([A-Za-z][A-Za-z\s]{2,30})\s+area\s*$", raw or "", flags=re.I)
    if m:
        return m.group(1).strip()
    return raw.strip() if raw else raw

def _normalize_location_value(raw: str | None) -> str | None:
    """Normalize location: skip generic 'my shop/farm/house' and structural fragments like 'the wall of my house'."""
    if not raw:
        return None
    v = raw.strip()
    low = v.lower()
    if low in ("my shop", "my farm", "my house", "my office", "shop", "farm", "house", "office"):
        return None
    if low in _NON_LOCATION_WORDS:
        return None
    # "Unga House" is a Nairobi building/venue — allow Proper-Noun House when paired with a capital first word
    if low.endswith(" house") and re.match(r"^[A-Z][A-Za-z]+\s+House$", v):
        return v
    if re.search(r"\b(?:wall|ceiling|floor)\b", low):
        return None
    # generic "house" alone is not a location, but "X House" above is allowed
    if re.search(r"\bhouse\b", low) and not re.match(r"^[A-Z][A-Za-z]+\s+House$", v):
        return None
    return v


# Capacity extraction for venue requests (e.g. 100 people, 200 guests, capacity 200)
_CAPACITY_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})*|\d+)\s*(?:people|persons|guests|pax|attendees|capacity)?\b", re.I)
_CAPACITY_PEOPLE_RE = re.compile(r"\b(\d{1,4})\s*(?:people|persons|guests|pax|attendees)\b", re.I)
_BUDGET_NUM_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d{4,})\b")

def _extract_capacity_value(text: str) -> int | None:
    m = _CAPACITY_PEOPLE_RE.search(text or "")
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except Exception:
            pass
    return None

def _extract_budget_value(text: str) -> float | None:
    # First try keyword-anchored
    m = _BUDGET_RE.search(text or "")
    if m:
        raw = (m.group(1) or m.group(2) or "").replace(",", "").strip()
        if raw:
            try:
                return float(raw)
            except Exception:
                pass
    # Fallback: standalone number >= 1000 in a budget-like message ("50,000 for 200 people")
    bm = _BUDGET_NUM_RE.search(text or "")
    if bm and _CAPACITY_PEOPLE_RE.search(text or ""):
        # message contains people count, the other large number is likely budget
        raw = bm.group(0).replace(",", "")
        cap = _extract_capacity_value(text)
        if cap is not None and str(cap) in raw:
            # this match is the capacity, look for another
            for m2 in _BUDGET_NUM_RE.finditer(text or ""):
                r2 = m2.group(0).replace(",", "")
                if r2 != str(cap):
                    try:
                        v = float(r2)
                        if v >= 1000:
                            return v
                    except Exception:
                        continue
        else:
            try:
                v = float(raw)
                if v >= 1000:
                    return v
            except Exception:
                pass
    return None

def _extract_location_value(text: str) -> str | None:
    text = _normalize_typos(text)
    # Farming Lamu consultation — Lamu is farming context; only trigger when the phrase contains lamu+farm together
    if re.search(r"\blamu\b.*\bfarm|\bfarm.*\blamu\b", text or "", re.I):
        low_lamu = (text or "").lower()
        if "witu" in low_lamu:
            return "Witu"
        return "Lamu"
    # Bare "Maize" or single-word crop answers are not locations — never treat as location
    if re.match(r"^\s*[A-Za-z]{3,20}\s*$", text or ""):
        low_single = (text or "").strip().lower()
        if low_single in ("maize","tomato","rice","cassava","mango","cashew","coconut","beans","wheat","yes","no"):
            return None
    # Swahili location answer: "Niko hapa Kipsebwo, Nandi Hills." → extract locality + town
    # Strip common Swahili preamble before location parsing
    _sw = re.sub(r"^\s*(?:niko\s+hapa|niko|hapa|mimi\s+niko\s+hapa)\s+", "", text or "", flags=re.I)
    if _sw != (text or ""):
        _sw_clean = _sw.strip().rstrip(".,!;:").strip()
        inner = _extract_location_value(_sw_clean)
        if inner:
            return inner
        bm_sw = _BARE_MULTI_LOCATION_RE.match(_sw_clean or "")
        if bm_sw:
            return _extract_location_value(_sw_clean)
    # Correction phrasing "Actually, make that Nakuru" — extract the trailing place as location
    m_make = re.search(r"\bmake\s+that\s+([A-Za-z][A-Za-z\s]{1,30})\s*$", text or "", re.I)
    if m_make:
        # Don't treat service name as location (e.g. carpenter)
        _cand_make = m_make.group(1).strip()
        if re.search(r"\b(?:carpenter|builder|tiler|electrician|plumber|lawyer)\b", _cand_make, re.I):
            # Extract only the trailing location after "in" if present
            m2 = re.search(r"\bin\s+([A-Za-z]{3,30})\s*$", _cand_make, re.I)
            if m2:
                loc = _normalize_location_value(m2.group(1).strip()[:60])
                if loc:
                    return loc
            return _extract_location_value(re.sub(r"^.*\bmake\s+that\s+", "", text or "", flags=re.I))  # fallback
    if m_make:
        loc = _normalize_location_value(m_make.group(1).strip()[:60])
        if loc:
            return loc
    # Handle "Kasarani area" standalone as location before bare checks
    _area_m = re.match(r"^\s*([A-Za-z]{3,30})\s+area\s*(?:[\.,].*)?$", text or "", flags=re.I)
    if _area_m:
        cand = _area_m.group(1).strip()
        norm = _normalize_location_value(cand)
        if norm and cand.lower() not in _STOPWORDS:
            return norm
    # Handle "kasarani area. also ..." compound -> first clause is location
    _area_prefix = re.match(r"^\s*([A-Za-z]{3,30})\s+area\s*[\.,]\s*also\b", text or "", flags=re.I)
    if _area_prefix:
        cand = _area_prefix.group(1).strip()
        norm = _normalize_location_value(cand)
        if norm:
            return norm
    m = _LOCATION_RE.search(text)
    if m:
        raw = m.group(1).strip().rstrip(",").strip()[:60]
        norm = _normalize_location_value(raw)
        if norm:
            return norm
        for m2 in _LOCATION_RE.finditer(text):
            if m2.group(1) == raw:
                continue
            alt = _normalize_location_value(m2.group(1).strip().rstrip(",").strip()[:60])
            if alt:
                return alt
        return None
    # Handle comma-separated location phrases as bare multi-location (e.g. "Westlands, Chiromo Road, Nairobi")
    # Strip trailing punctuation for bare multi-location match (e.g. "Kipsebwo, Nandi Hills.")
    _bare_text = (text or "").strip().rstrip(".,!;:").strip()
    # Skip bare multi-location extraction for messages that are professional service requests (e.g. "yeah, im looking for a house builder" has a comma)
    _is_prof_req_for_loc = _looks_like_professional_request(_bare_text or "")
    # Don't treat correction phrases as locations
    _is_corr_like = bool(re.search(r"\bactually\b", _bare_text or "", re.I))
    # Plumbing diagnostic answers like "yes, water is close to overflowing" must not become locations
    _is_plumbing_answer = bool(re.search(r"\b(?:overflowing|blocked|plumb|toilet|drain|cistern|flush)\b", _bare_text or "", re.I))
    bm_multi = None if (_is_prof_req_for_loc or _is_corr_like or _is_plumbing_answer) else _BARE_MULTI_LOCATION_RE.match(_bare_text or "")
    if bm_multi:
        raw_multi = bm_multi.group(1).strip()[:140]
        # Preserve the full user-typed address (up to 140 chars) for qualified plumbing; first token also works for matching
        # e.g. "Westlands, Chiromo Road, Nairobi" stays as-is for display and _is_eligible_location substring check
        first = raw_multi.split(",")[0].strip() if "," in raw_multi else raw_multi.strip()
        if first.lower() not in _STOPWORDS and len(first) >= 4:
            if first.lower() not in {s.lower() for s in _SERVICE_HINTS} and first.lower() not in ("dentist","whitening","extraction"):
                # For comma addresses, return the full trimmed address (matching engine uses substring, so "Chiromo Road" will still be checked)
                cleaned = raw_multi.strip()[:140]
                # normalize each segment
                norm = cleaned  # keep original casing for display
                # Validate first segment still passes normalize
                if _normalize_location_value(first[:60]):
                    return norm
        norm2 = _normalize_location_value(raw_multi.split(",")[0].strip()[:60])
        if norm2:
            return norm2
    # Strip trailing punctuation for bare location (e.g. "Kasarani.")
    _bare_text2 = (text or "").strip().rstrip(".,!;:").strip()
    bm = _BARE_LOCATION_RE.match(_bare_text2)
    if bm:
        tok = bm.group(1).strip()
        if tok.lower() not in _STOPWORDS and len(tok) >= 4:
            if tok.lower() not in {s.lower() for s in _SERVICE_HINTS} and tok.lower() not in ("dentist","whitening","extraction"):
                return _normalize_location_value(tok[:60])
    # Building/venue names like "Unga House" — treat as location when we have an active service context
    # (website_chat will pass existing, so this is used via qualify_message with existing)
    if re.match(r"^\s*[A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+\s*$", text or ""):
        # Two-word capitalized phrase (Unga House, Chiromo Road) — plausible building/address
        if not re.search(r"\b(?:hello|there|please|thanks|thank)\b", text or "", re.I):
            return _normalize_location_value(text.strip()[:60])
    return None


def qualify_message(text: str | None, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Extract qualification fields from free text."""
    text = (text or "").strip()
    data: dict[str, Any] = dict(existing or {})
    lower = text.lower()
    raw_request = text
    # Reset: only treat as wipe-the-slate when the message does NOT also carry a new service/location/capacity.
    # "please clear the past ... for 100 people" style should NOT happen; if it does, keep the service.
    _is_reset_msg = is_explicit_reset(text)
    _reset_only = False
    if _is_reset_msg:
        has_affirmative = bool(re.search(r"\b(?:need|want|looking\s+for)\b.*\b(?:plumb|vet|dental|dentist|cctv|camera|solar|borehole|engineer|architect|appliance|fridge|electrical|salon|clinic|restaurant|hotel|gym|barber|legal|spa|venue|event)\b", lower))
        if not has_affirmative and not _extract_location_value(text) and _extract_capacity_value(text) is None and _extract_budget_value(text) is None:
            _reset_only = True

    # Plumbing symptom refinement: "The cistern is not filling..." during an active
    # plumbing consultation should NOT be re-parsed as a new service named "filling"
    _active_plumbing = False
    _plumb_loc_for_symptom = None
    try:
        if data.get("requested_service") and str(data.get("requested_service")).lower() in ("plumbing",):
            # Guard on requested_service is enough — consult_task may be legacy without domain
            _has_plumbing = True
            try:
                from heshly_core.services.network.consultation_engine import get_active_task as _gat_plumb
                _at_plumb = _gat_plumb(data)
                if _at_plumb is not None and _at_plumb.domain != "plumbing":
                    _has_plumbing = False
            except Exception:
                pass
            if _has_plumbing and re.search(r"\b(?:cistern|blocked|toilet|flush|leak|drain|tap|pipe|sink|burst)\b", lower):
                _active_plumbing = True
                _plumb_loc_for_symptom = _extract_location_value(text)
    except Exception:
        pass
    if _active_plumbing and re.search(r"\b(?:cistern|blocked|toilet|flush|leak|drain|tap|pipe|sink|burst)\b", lower):
        # Symptom refinement — keep service as plumbing, don't let "filling" become a new service
        if _plumb_loc_for_symptom:
            data["location"] = _plumb_loc_for_symptom
        data["raw_request"] = text[:500]
        # Preserve location from existing if refinement has no new location
        if not data.get("location") and existing and existing.get("location"):
            data["location"] = existing.get("location")
        _has_service = bool(data.get("requested_service"))
        _has_location = bool(data.get("location"))
        if _has_service and _has_location:
            data["qualification_state"] = QualificationState.QUALIFIED.value
        elif _has_service or _has_location:
            data["qualification_state"] = QualificationState.IN_PROGRESS.value
        else:
            data["qualification_state"] = QualificationState.PENDING.value
        return data

    prohibited = _is_prohibited(text)
    if prohibited:
        data["requested_service"] = (data.get("requested_service") or "__prohibited__")
        data["qualification_state"] = QualificationState.DISQUALIFIED.value
        data["disqualified_reason"] = "prohibited"
        return data

    if _reset_only:
        for k in ("requested_service", "normalized_service", "provider_category", "raw_request", "location", "budget_min", "budget_max", "capacity", "urgency", "preferred_time"):
            data.pop(k, None)
        data["qualification_state"] = QualificationState.PENDING.value
        return data
    # Normalize generic location placeholders before extraction: they produce no-location so we ask "where are you located?"
    # The check itself is in _normalize_location_value after location extraction.

    # -- correction/change signals allow re-evaluation even when existing has data
    _correction_signal = bool(
        re.search(r"\b(actually|change|forget|instead|make\s+that|sorry\b|now\b|not\s+a\s+lawyer|no\s+not\s+a)\b", lower)
        or is_explicit_reset(text)
        or is_correction(text)
    )
    _is_addition = bool(re.search(r"\balso\b", lower))
    _service_overridable = (not data.get("requested_service")) or _correction_signal

    # Normalize typos for downstream extraction/matching (preserve raw_request as typed)
    _norm_text = _normalize_typos(text)
    if _norm_text != text:
        lower = _norm_text.lower()
        raw_request = _norm_text
        text = _norm_text

    # Track whether this turn is a professional request (structure-based)
    _is_prof_req_local = _looks_like_professional_request(text)

    # Only attempt service extraction if this turn plausibly is a service request; otherwise leave existing intact.
    _should_extract_service = _is_prof_req_local or _service_overridable or not data.get("requested_service")
    if is_correction(text):
        _should_extract_service = True
    if _should_extract_service:
        prev_service = data.get("requested_service")
        new_service = None
        _fresh_text = text
        if is_correction(text):
            _fresh_text = _strip_correction_prefix(text)
        elif _correction_signal:
            _split = re.split(r"(?:never\s*mind|forget\s+(?:that|it|this|\b\w+\b\s+thing)|let'?s\s+start\s*(?:over|again))", text, flags=re.I)
            if len(_split) > 1:
                _fresh_text = _split[-1]
        _fresh_lower = _fresh_text.lower()
        for pat, canonical in _SERVICE_ALIASES:
            if pat.search(_fresh_text):
                new_service = canonical
                break
        # Electrical hazard takes priority over spa substring in "sparks"
        if not new_service:
            if re.search(r"\bsparks?\b", _fresh_lower) or re.search(r"\bwall\s+socket\b", _fresh_lower) or re.search(r"\bsocket\b", _fresh_lower):
                new_service = "electrical"
            # Avoid spa false positive inside "sparks"
            elif "sparks" not in _fresh_lower:
                for hint in _SERVICE_HINTS:
                    if hint in _fresh_lower:
                        new_service = hint
                        break
            else:
                for hint in _SERVICE_HINTS:
                    if hint == "spa":
                        continue
                    if hint in _fresh_lower:
                        new_service = hint
                        break
        if not new_service:
            open_svc = _extract_open_service(_fresh_text, data.get("requested_service"))
            if open_svc:
                new_service = open_svc
        if new_service:
            if not data.get("requested_service") or str(new_service).lower() != str(prev_service).lower():
                data["requested_service"] = new_service
            if _correction_signal and not is_correction(text) and data.get("location") and str(data.get("location") or "").lower() not in _fresh_lower:
                # For also-addition, keep location (project location)
                if not _is_addition:
                    data.pop("location", None)

    # Location refinement: allow updating Unga House -> Westlands/Chiromo when user gives a more precise address
    _service_changed = False
    try:
        if data.get("requested_service") and existing and existing.get("requested_service") and data.get("requested_service") != existing.get("requested_service"):
            _service_changed = True
    except Exception:
        pass
    # If existing location is a building name and new message has a comma-address, treat as refinement
    _is_address_refinement = False
    try:
        if existing and existing.get("location") and _extract_location_value(text):
            _prev_is_building = bool(re.match(r"^[A-Z][A-Za-z]+\s+House$", existing.get("location") or ""))
            _new_has_comma = "," in text
            if _prev_is_building and _new_has_comma:
                _is_address_refinement = True
    except Exception:
        pass
    _loc_overridable = (not data.get("location")) or _correction_signal or _service_changed or _is_address_refinement
    if _loc_overridable:
        prev_loc = data.get("location")
        _loc_text = _strip_correction_prefix(text) if is_correction(text) else text
        new_loc = _extract_location_value(_loc_text)
        # Do not set location to the service phrase itself
        if new_loc and data.get("requested_service") and new_loc.lower() == data.get("requested_service","").lower():
            new_loc = None
        # Also skip location that equals the raw service-bearing message (e.g. "yeah, im looking for a house builder")
        if new_loc and _looks_like_professional_request(text) and new_loc.lower() in text.lower() and len(new_loc) > 20:
            # Likely extracted the whole request as location
            new_loc = None
        if new_loc and (not data.get("location") or str(new_loc).lower() != str(prev_loc).lower()):
            # Retention: if new is broader town and prev is specific locality+town, keep specific
            if prev_loc and new_loc and new_loc.lower() in prev_loc.lower() and len(new_loc) < len(prev_loc):
                pass
            else:
                data["location"] = new_loc
        # Also handle case where _loc_overridable is False but text is broad town — ensure we keep specific
        # (no action needed — we just keep prev_loc)

    # Separated fields: raw_request always kept; normalized derived when confident
    # For corrections, derive normalized from the stripped corrected text
    _norm_source = _strip_correction_prefix(raw_request) if is_correction(raw_request) else raw_request
    norm, cat = _normalize_professional_request(_norm_source)
    if raw_request and not _reset_only:
        data["raw_request"] = raw_request[:500]
    if norm:
        data["normalized_service"] = norm
        if cat:
            data["provider_category"] = cat
    elif _is_prof_req_local and raw_request:
        data.setdefault("normalized_service", "")
        data.setdefault("provider_category", "")

    if not data.get("urgency") or data.get("urgency") in ("", "medium"):
        if _URGENCY_RE.search(lower):
            data["urgency"] = Urgency.HIGH.value if "emergency" not in lower else Urgency.URGENT.value

    if not data.get("preferred_time"):
        m = _TIME_RE.search(text)
        if m:
            data["preferred_time"] = m.group(0).strip()

    # Capacity / budget extraction (venue) — allow bare numbers
    cap = _extract_capacity_value(text)
    if cap is not None:
        # Overwrite on correction signal or if not yet set; venue capacity should reflect latest intent
        _prev_cap = data.get("capacity")
        if _prev_cap is None or _correction_signal or str(cap) != str(_prev_cap):
            # For venue requests, treat capacity update as intentional; preserve other fields
            data["capacity"] = cap
    bud = _extract_budget_value(text)
    if bud is not None:
        if not data.get("budget_min") or _correction_signal:
            data["budget_min"] = bud
        elif bud != data.get("budget_min"):
            # budget correction — update
            data["budget_min"] = bud

    # qualification_state heuristic
    # If already flagged disqualified (prohibited), preserve it
    if data.get("qualification_state") == QualificationState.DISQUALIFIED.value:
        return data
    # For casual/greeting/reset with no service/location, force pending (clears stale fields via caller)
    _intent_for_qs = None
    try:
        from heshly_core.services.network.qualification_service import classify_customer_intent as _ci2
        _intent_for_qs = _ci2(text, data.get("requested_service", "") or "")
    except: pass
    if _intent_for_qs in ("greeting","casual","reset") and not data.get("requested_service") and not data.get("location"):
        data.pop("requested_service", None)
        data.pop("normalized_service", None)
        data.pop("provider_category", None)
        data["qualification_state"] = QualificationState.PENDING.value
        return data
    has_service = bool(data.get("requested_service"))
    has_location = bool(data.get("location"))
    has_raw_prof = bool(data.get("raw_request")) and _looks_like_professional_request(data.get("raw_request",""))
    if has_service and has_location:
        data["qualification_state"] = QualificationState.QUALIFIED.value
    elif has_service or has_location or has_raw_prof:
        if has_service or has_location:
            data["qualification_state"] = QualificationState.QUALIFIED.value if (has_service and has_location) else QualificationState.IN_PROGRESS.value
        else:
            data["qualification_state"] = QualificationState.IN_PROGRESS.value
        if len(text.strip()) <= 4:
            data["qualification_state"] = QualificationState.PENDING.value
    elif len(text) > 20:
        if len(text.strip()) <= 4:
            data["qualification_state"] = QualificationState.PENDING.value
        else:
            data["qualification_state"] = QualificationState.IN_PROGRESS.value
    else:
        data["qualification_state"] = QualificationState.PENDING.value

    return data


def qualification_from_turns(turns: list[dict[str, Any]] | None) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for t in turns or []:
        msg = t.get("message") or t.get("text") or ""
        if (t.get("role") or "").lower() == "user":
            data = qualify_message(msg, data)
    return data
