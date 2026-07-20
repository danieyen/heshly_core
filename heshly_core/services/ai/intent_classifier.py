from heshly_core.models.intent import Intent, IntentResult


class IntentClassifier:
    """
    Rule-based intent classifier for the Heshly MVP.

    This implementation is intentionally deterministic.
    Later versions will delegate classification to an LLM
    while preserving the same interface.
    """

    KEYWORDS = {
        Intent.BOOK_APPOINTMENT: [
            "book",
            "appointment",
            "schedule",
            "reserve",
        ],
        Intent.RESCHEDULE_APPOINTMENT: [
            "reschedule",
            "change appointment",
            "move appointment",
        ],
        Intent.CANCEL_APPOINTMENT: [
            "cancel",
            "remove appointment",
        ],
        Intent.PRICE_INQUIRY: [
            "price",
            "cost",
            "fee",
            "charges",
        ],
        Intent.BUSINESS_HOURS: [
            "hours",
            "open",
            "closing",
            "working hours",
        ],
        Intent.LOCATION: [
            "where",
            "location",
            "address",
            "directions",
        ],
        Intent.HUMAN_SUPPORT: [
            "human",
            "agent",
            "person",
            "staff",
        ],
        Intent.GREETING: [
            "hello",
            "hi",
            "good morning",
            "good afternoon",
            "hey",
        ],
    }

    def classify(self, message: str) -> IntentResult:
        text = message.lower().strip()

        for intent, keywords in self.KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return IntentResult(
                    intent=intent,
                    confidence=0.95,
                    reasoning=f"Matched keywords for {intent.value}.",
                )

        return IntentResult(
            intent=Intent.UNKNOWN,
            confidence=0.20,
            reasoning="No keyword matched.",
        )