from heshly_core.models.decision_context import DecisionContext

from heshly_core.services.qualification.qualification_engine import (
    QualificationEngine,
)

from .action_planner import ActionPlanner
from .business_rules import BusinessRules
from .completeness_checker import CompletenessChecker
from .entity_extractor import EntityExtractor
from .intent_classifier import IntentClassifier


class DecisionEngine:
    """
    Coordinates the complete AI decision pipeline.

    Qualification runs alongside the existing booking decision
    pipeline. Qualification handles lead/customer readiness while
    the existing booking components handle service/date/time
    completeness, business rules, and booking actions.
    """

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.completeness_checker = CompletenessChecker()
        self.business_rules = BusinessRules()
        self.action_planner = ActionPlanner()
        self.qualification_engine = QualificationEngine()

    def process(
        self,
        message: str,
        collected_data: dict[str, object] | None = None,
        required_fields: list[str] | None = None,
        customer_id: str = "unknown",
    ) -> DecisionContext:

        context = DecisionContext(
            raw_message=message
        )

        # -------------------------------------------------
        # 1. Detect intent
        # -------------------------------------------------

        context.intent = self.intent_classifier.classify(
            context.raw_message
        )

        # -------------------------------------------------
        # 2. Extract entities
        # -------------------------------------------------

        context.entities = self.entity_extractor.extract(
            context.raw_message
        )

        # -------------------------------------------------
        # 3. Qualification
        # -------------------------------------------------

        if collected_data is None:
            collected_data = {
                "customer_name": (
                    context.entities.customer_name
                ),
                "phone": context.entities.phone,
                "email": context.entities.email,
                "service": context.entities.service,
                "date": context.entities.date,
                "time": context.entities.time,
            }

        if required_fields is None:
            required_fields = [
                "customer_name",
                "phone",
            ]

        (
            context.qualification,
            context.qualification_action,
            context.qualification_response,
        ) = self.qualification_engine.qualify(
            customer_id=customer_id,
            message=message,
            collected_data=collected_data,
            required_fields=required_fields,
        )

        # -------------------------------------------------
        # 4. Booking completeness
        # -------------------------------------------------

        context.completeness = (
            self.completeness_checker.check(
                context.intent.intent,
                context.entities,
            )
        )

        # -------------------------------------------------
        # 5. Business rules
        # -------------------------------------------------

        if context.completeness.complete:
            context.rules = self.business_rules.evaluate(
                context.intent.intent,
                context.entities,
            )

        # -------------------------------------------------
        # 6. Existing booking action planner
        # -------------------------------------------------

        context.action = self.action_planner.plan(
            context.intent.intent,
            context.completeness,
            context.rules,
        )

        return context

    def health(self):
        return {
            "service": "decision_engine",
            "status": "healthy",
        }
