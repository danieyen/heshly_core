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
            r"(today|tomorrow|next\s+\w+)",
            lower,
        )

        if date_match:
            entities.date = date_match.group(1)

        time_match = re.search(
            r"\b\d{1,2}(:\d{2})?\s?(am|pm)\b",
            lower,
        )

        if time_match:
            entities.time = time_match.group(0)

        return entities