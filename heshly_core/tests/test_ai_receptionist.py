from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:

    id: str
    name: str


@dataclass
class IntentResult:

    intent: str
    confidence: float


@dataclass
class Appointment:

    id: str
    service: str
    status: str


class IntentClassifier:

    def classify(
        self,
        message: str,
    ) -> IntentResult:

        return IntentResult(
            intent="BOOK_APPOINTMENT",
            confidence=0.98,
        )


class EntityExtractor:

    def extract(
        self,
        message: str,
    ):

        return {
            "service": "Consultation",
            "date": "Tomorrow",
            "time": "10:00 AM",
        }


class CompletenessChecker:

    def check(
        self,
        entities: dict,
    ) -> bool:

        return all(
            entities.values()
        )


class DecisionEngine:

    def decide(
        self,
        complete: bool,
    ) -> str:

        return (
            "BOOK"
            if complete
            else "ASK_MORE"
        )


class Scheduler:

    def book(
        self,
        entities: dict,
    ) -> Appointment:

        return Appointment(
            id="APT-001",
            service=entities["service"],
            status="Booked",
        )


class NotificationService:

    def send(
        self,
        appointment: Appointment,
    ) -> bool:

        return True


def test_ai_receptionist():

    print("\n================================")
    print("AI Receptionist Test")
    print("================================\n")

    classifier = IntentClassifier()

    extractor = EntityExtractor()

    checker = CompletenessChecker()

    engine = DecisionEngine()

    scheduler = Scheduler()

    notifier = NotificationService()

    customer = Customer(
        id="CUST-001",
        name="John Doe",
    )

    message = (
        "I want to book a consultation "
        "tomorrow at 10 AM."
    )

    intent = classifier.classify(
        message,
    )

    assert intent.intent == "BOOK_APPOINTMENT"

    print("✅ Intent Classified")

    entities = extractor.extract(
        message,
    )

    assert entities["service"] == "Consultation"

    print("✅ Entities Extracted")

    complete = checker.check(
        entities,
    )

    assert complete is True

    print("✅ Completeness Checked")

    action = engine.decide(
        complete,
    )

    assert action == "BOOK"

    print("✅ Decision Made")

    appointment = scheduler.book(
        entities,
    )

    assert appointment.status == "Booked"

    print("✅ Appointment Created")

    assert notifier.send(
        appointment,
    )

    print("✅ Confirmation Sent")

    print("\n🎉 AI RECEPTIONIST TEST PASSED\n")