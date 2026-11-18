import re

from heshly_core.models.conversation import ExtractedEntities


class EntityExtractor:
    """
    Basic entity extractor for the MVP.

    Later this will be replaced or enhanced with an LLM
    while keeping the same interface.
    """

    def extract(self, message: str) -> ExtractedEntities:
        entities = ExtractedEntities()

        lower = message.lower()

        service_patterns = [
            "dental cleaning",
            "consultation",
            "checkup",
            "whitening",
            "filling",
        ]

        for service in service_patterns:
            if service in lower:
                entities.service = service.title()
                break

        date_match = re.search(
            r"(today|tomorrow|next\s+\w+|\d{4}-\d{2}-\d{2})",
            lower,
        )

        if date_match:
            entities.date = date_match.group(1)
        # also try ISO in original message (case-sensitive preserved)
        if not entities.date:
            m2 = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message)
            if m2:
                entities.date = m2.group(0)

        time_match = re.search(
            r"\b\d{1,2}(:\d{2})?\s?(am|pm)\b",
            lower,
        )

        if time_match:
            entities.time = time_match.group(0)

        # — customer name — explicit patterns only (avoid false positives on "this week")
        # "my name is Jane Doe" / "I'm Jane Doe" / "I am Jane Doe" / "name is Jane Doe"
        # Bound capture to stop before words like "email", "phone", "interested", "want"
        stop_words = r"(?:email|phone|interested|want|need|like|for|with|and|at|on|in)"
        name_patterns = [
            rf"my name is\s+([a-z][a-z\s'.-]*?)(?=\s+{stop_words}\b|,|$)",
            rf"\bi am\s+([a-z][a-z\s'.-]*?)(?=\s+{stop_words}\b|,|email|\s*\+?\d|$)",
            rf"\bi'm\s+([a-z][a-z\s'.-]*?)(?=\s+{stop_words}\b|,|email|\s*\+?\d|$)",
            rf"\bname is\s+([a-z][a-z\s'.-]*?)(?=\s+{stop_words}\b|,|$)",
        ]
        for pat in name_patterns:
            m = re.search(pat, lower)
            if m:
                raw = m.group(1).strip().strip(" .,-")
                # fallback: also strip trailing fragment if still polluted
                raw = re.split(r"\s+(?:email|phone|interested|want)\b", raw)[0].strip(" .,-")
                parts = [p for p in raw.split() if len(p) > 1]
                if 1 <= len(parts) <= 3:
                    entities.customer_name = " ".join(w.capitalize() for w in parts)
                    break

        # — phone — E.164 / Kenyan / generic international
        phone_patterns = [
            r"(\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3,4})",
            r"(\+254\d{9})",
            r"(0?7\d{8})",
        ]
        for pat in phone_patterns:
            m = re.search(pat, message)  # use original (preserve +)
            if m:
                # take the longest cleaned match
                raw = re.sub(r"[\s\-]", "", m.group(1).strip())
                if len(raw) >= 9:
                    entities.phone = raw
                    break

        # — email —
        email_m = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", message)
        if email_m:
            entities.email = email_m.group(0).lower()

        return entities