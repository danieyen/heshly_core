from heshly_core.models.learning import (
    ConversationOutcome,
    FeedbackRating,
    PerformanceMetrics,
)

from heshly_core.services.learning.learning_conversation_flow import (
    LearningConversationFlow,
)

from heshly_core.services.learning.performance_metrics_engine import (
    PerformanceMetricsEngine,
)

from heshly_core.services.learning.recommendation_engine import (
    RecommendationEngine,
)


class LearningEngine:
    """
    Main integration layer for Heshly learning.

    Provides one interface for:
    - conversation learning
    - metrics generation
    - improvement recommendations
    """

    def __init__(self):

        self.conversation_flow = (
            LearningConversationFlow()
        )

        self.metrics_engine = (
            PerformanceMetricsEngine()
        )

        self.recommendation_engine = (
            RecommendationEngine()
        )


    def process_conversation(
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
    ):

        return self.conversation_flow.execute(
            conversation_id=conversation_id,
            customer_id=customer_id,
            outcome=outcome,
            feedback_rating=feedback_rating,
            feedback_comment=feedback_comment,
            ai_engine=ai_engine,
            ai_decision=ai_decision,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
        )


    def generate_metrics(
        self,
        *,
        total_conversations: int,
        booked: int,
        qualified: int,
        handovers: int,
        failures: int,
        corrections: int,
        average_feedback: float,
    ) -> PerformanceMetrics:

        return self.metrics_engine.calculate(
            total_conversations=total_conversations,
            booked=booked,
            qualified=qualified,
            handovers=handovers,
            failures=failures,
            corrections=corrections,
            average_feedback=average_feedback,
        )


    def generate_recommendations(
        self,
        metrics: PerformanceMetrics,
    ):

        return self.recommendation_engine.generate(
            metrics=metrics
        )