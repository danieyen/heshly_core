from heshly_core.models.learning import (
    PerformanceMetrics,
)


class PerformanceMetricsEngine:
    """
    Calculates operational performance metrics.
    """

    def calculate(
        self,
        *,
        total_conversations: int,
        booked: int,
        qualified: int,
        handovers: int,
        failures: int,
        corrections: int,
        average_feedback: float = 0.0,
    ) -> PerformanceMetrics:

        booking_rate = (
            booked / total_conversations
            if total_conversations
            else 0.0
        )

        qualification_rate = (
            qualified / total_conversations
            if total_conversations
            else 0.0
        )

        escalation_rate = (
            handovers / total_conversations
            if total_conversations
            else 0.0
        )

        correction_rate = (
            corrections / total_conversations
            if total_conversations
            else 0.0
        )

        return PerformanceMetrics(

            total_conversations=total_conversations,

            booked_conversations=booked,

            qualified_conversations=qualified,

            handovers=handovers,

            failures=failures,

            human_corrections=corrections,

            average_feedback_score=average_feedback,

            booking_rate=booking_rate,

            qualification_rate=qualification_rate,

            escalation_rate=escalation_rate,

            correction_rate=correction_rate,
        )