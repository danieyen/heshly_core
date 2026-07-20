from heshly_core.models.qualification import (
    UrgencyLevel,
)


class UrgencyAssessment:
    """
    Determines the urgency of a customer's request.
    """

    EMERGENCY_KEYWORDS = {
        "can't breathe",
        "cannot breathe",
        "unconscious",
        "bleeding heavily",
        "severe bleeding",
        "heart attack",
        "stroke",
        "collapsed",
    }

    HIGH_KEYWORDS = {
        "severe pain",
        "swollen",
        "swelling",
        "broken",
        "accident",
        "emergency",
        "urgent",
    }

    MEDIUM_KEYWORDS = {
        "pain",
        "hurts",
        "fever",
        "infection",
    }

    def assess(
        self,
        message: str,
    ) -> UrgencyLevel:

        text = message.lower()

        if self._contains_any(
            text,
            self.EMERGENCY_KEYWORDS,
        ):
            return UrgencyLevel.EMERGENCY

        if self._contains_any(
            text,
            self.HIGH_KEYWORDS,
        ):
            return UrgencyLevel.HIGH

        if self._contains_any(
            text,
            self.MEDIUM_KEYWORDS,
        ):
            return UrgencyLevel.MEDIUM

        return UrgencyLevel.LOW

    @staticmethod
    def _contains_any(
        text: str,
        keywords: set[str],
    ) -> bool:

        return any(
            keyword in text
            for keyword in keywords
        )