from heshly_core.models.decision_context import DecisionContext

from .action_planner import ActionPlanner
from .business_rules import BusinessRules
from .completeness_checker import CompletenessChecker
from .entity_extractor import EntityExtractor
from .intent_classifier import IntentClassifier


class DecisionEngine:
    """
    Coordinates the entire AI decision pipeline.
    """

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.completeness_checker = CompletenessChecker()
        self.business_rules = BusinessRules()
        self.action_planner = ActionPlanner()

    def process(self, message: str) -> DecisionContext:

        context = DecisionContext(raw_message=message)

        # 1. Detect intent
        context.intent = self.intent_classifier.classify(
            context.raw_message
        )

        # 2. Extract entities
        context.entities = self.entity_extractor.extract(
            context.raw_message
        )

        # 3. Check completeness
        context.completeness = self.completeness_checker.check(
            context.intent.intent,
            context.entities,
        )

        # 4. Validate business rules only if complete
        if context.completeness.complete:
            context.rules = self.business_rules.evaluate(
                context.intent.intent,
                context.entities,
            )

        # 5. Plan the next action
        context.action = self.action_planner.plan(
            context.intent.intent,
            context.completeness,
            context.rules,
        )

        return context