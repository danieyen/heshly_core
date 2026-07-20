from heshly_core.models.learning import (
    ConversationOutcome,
    FeedbackRating,
    FailureType,
)

from heshly_core.services.learning.conversation_outcome_tracker import (
    ConversationOutcomeTracker,
)

from heshly_core.services.learning.customer_feedback_collector import (
    CustomerFeedbackCollector,
)

from heshly_core.services.learning.ai_decision_logger import (
    AIDecisionLogger,
)

from heshly_core.services.learning.error_failure_tracker import (
    ErrorFailureTracker,
)

from heshly_core.services.learning.human_correction_tracker import (
    HumanCorrectionTracker,
)


class LearningConversationFlow:
    """
    Coordinates all learning activities
    related to a conversation.
    """

    def __init__(self):

        self.outcome_tracker = (
            ConversationOutcomeTracker()
        )

        self.feedback_collector = (
            CustomerFeedbackCollector()
        )

        self.decision_logger = (
            AIDecisionLogger()
        )

        self.failure_tracker = (
            ErrorFailureTracker()
        )

        self.correction_tracker = (
            HumanCorrectionTracker()
        )


    def execute(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        outcome: ConversationOutcome,
        feedback_rating: FeedbackRating | None = None,
        feedback_comment: str | None = None,
        ai_engine: str | None = None,
        ai_decision: str | None = None,
        ai_confidence: float | None = None,
        ai_reasoning: str | None = None,
        failure_type: FailureType | None = None,
        failure_source: str | None = None,
        failure_message: str | None = None,
    ):

        result = {}


        result["outcome"] = (
            self.outcome_tracker.track(
                conversation_id=conversation_id,
                customer_id=customer_id,
                outcome=outcome,
            )
        )


        if feedback_rating:

            result["feedback"] = (
                self.feedback_collector.collect(
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    rating=feedback_rating,
                    comment=feedback_comment,
                )
            )


        if ai_engine and ai_decision:

            result["decision"] = (
                self.decision_logger.log(
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    engine=ai_engine,
                    decision=ai_decision,
                    confidence=ai_confidence or 0,
                    reasoning=ai_reasoning or "",
                )
            )


        if failure_type:

            result["failure"] = (
                self.failure_tracker.track(
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    failure_type=failure_type,
                    source=failure_source or "",
                    message=failure_message or "",
                )
            )


        return result