from heshly_core.models.learning import (
    PerformanceMetrics,
    Recommendation,
)


class RecommendationEngine:
    """
    Generates improvement recommendations
    from AI performance data.
    """

    def generate(
        self,
        *,
        metrics: PerformanceMetrics,
    ) -> list[Recommendation]:

        recommendations = []

        if metrics.booking_rate < 0.30:

            recommendations.append(
                Recommendation(
                    category="booking",
                    title="Improve booking conversion",
                    description=(
                        "Booking conversion is below target. "
                        "Review service availability, "
                        "qualification flow, and booking prompts."
                    ),
                    priority="high",
                    confidence=0.85,
                )
            )


        if metrics.escalation_rate > 0.25:

            recommendations.append(
                Recommendation(
                    category="handover",
                    title="Review escalation frequency",
                    description=(
                        "Human handovers are high. "
                        "Review AI confidence thresholds "
                        "and knowledge coverage."
                    ),
                    priority="medium",
                    confidence=0.80,
                )
            )


        if metrics.correction_rate > 0.15:

            recommendations.append(
                Recommendation(
                    category="ai_accuracy",
                    title="Review AI decisions",
                    description=(
                        "Human corrections are frequent. "
                        "Analyze corrected decisions "
                        "for possible rule or prompt improvements."
                    ),
                    priority="high",
                    confidence=0.90,
                )
            )


        if metrics.average_feedback_score < 3.5:

            recommendations.append(
                Recommendation(
                    category="customer_experience",
                    title="Improve customer experience",
                    description=(
                        "Customer satisfaction scores "
                        "are below target."
                    ),
                    priority="high",
                    confidence=0.75,
                )
            )


        return recommendations