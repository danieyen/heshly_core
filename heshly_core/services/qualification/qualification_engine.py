from heshly_core.models.qualification import (
    QualificationAction,
    QualificationResult,
)

from heshly_core.services.qualification.required_information_checker import (
    RequiredInformationChecker,
)

from heshly_core.services.qualification.eligibility_evaluator import (
    EligibilityEvaluator,
)

from heshly_core.services.qualification.urgency_assessment import (
    UrgencyAssessment,
)

from heshly_core.services.qualification.qualification_scorer import (
    QualificationScorer,
)

from heshly_core.services.qualification.qualification_status_manager import (
    QualificationStatusManager,
)

from heshly_core.services.qualification.qualification_conversation_flow import (
    QualificationConversationFlow,
)


class QualificationEngine:
    """
    Coordinates the complete qualification process.
    """

    def __init__(
        self,
        checker: RequiredInformationChecker | None = None,
        evaluator: EligibilityEvaluator | None = None,
        urgency: UrgencyAssessment | None = None,
        scorer: QualificationScorer | None = None,
        status_manager: QualificationStatusManager | None = None,
        flow: QualificationConversationFlow | None = None,
    ):
        self.checker = (
            checker
            or RequiredInformationChecker()
        )

        self.evaluator = (
            evaluator
            or EligibilityEvaluator()
        )

        self.urgency = (
            urgency
            or UrgencyAssessment()
        )

        self.scorer = (
            scorer
            or QualificationScorer()
        )

        self.status_manager = (
            status_manager
            or QualificationStatusManager()
        )

        self.flow = (
            flow
            or QualificationConversationFlow()
        )

    def qualify(
        self,
        customer_id: str,
        message: str,
        collected_data: dict[str, object],
        required_fields: list[str],
    ) -> tuple[
        QualificationResult,
        QualificationAction,
        str | None,
    ]:

        result = QualificationResult(
            customer_id=customer_id
        )

        # Check required information
        self.checker.check(
            collected_data,
            required_fields,
            result,
        )

        # Eligibility
        self.evaluator.evaluate(
            collected_data,
            result,
        )

        # Urgency
        result.urgency = self.urgency.assess(
            message
        )

        # Score
        self.scorer.score(
            result,
            len(required_fields),
        )

        # Status
        self.status_manager.update(
            result
        )

        # Conversation action
        action, response = (
            self.flow.next_step(
                result
            )
        )

        return (
            result,
            action,
            response,
        )