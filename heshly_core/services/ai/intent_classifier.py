from heshly_core.models.intent import Intent, IntentResult


class IntentClassifier:
    """
    Deterministic intent classifier for the Heshly MVP.

    Recognizes explicit booking language and natural
    service-based booking requests.
    """

    KEYWORDS = {
        Intent.BOOK_APPOINTMENT: [
            "book",
            "appointment",
            "schedule",
            "reserve",
            "make an appointment",
            "see the dentist",
            "see a dentist",
            "want a dental",
            "need a dental",
            "like a dental",
            "dental cleaning",
            "dental checkup",
            "dental consultation",
            "dental whitening",
            "dental filling",
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
            "how much",
        ],
        Intent.BUSINESS_HOURS: [
            "hours",
            "open",
            "closing",
            "working hours",
            "when are you open",
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
