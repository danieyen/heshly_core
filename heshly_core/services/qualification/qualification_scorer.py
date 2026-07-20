from heshly_core.models.qualification import (
    QualificationResult,
    UrgencyLevel,
)


class QualificationScorer:
    """
    Calculates a qualification score from 0 to 100.
    """

    def score(
        self,
        result: QualificationResult,
        required_fields: int,
    ) -> QualificationResult:

        score = 0.0

        # -------------------------
        # Information completeness
        # -------------------------

        if required_fields > 0:

            completed = (
                required_fields
                - len(result.missing_fields)
            )

            completeness = (
                completed / required_fields
            )

            score += completeness * 70

        # -------------------------
        # Eligibility
        # -------------------------

        if result.eligible:
            score += 20

        # -------------------------
        # Urgency
        # -------------------------

        urgency_bonus = {
            UrgencyLevel.LOW: 0,
            UrgencyLevel.MEDIUM: 2,
            UrgencyLevel.HIGH: 5,
            UrgencyLevel.EMERGENCY: 10,
        }

        score += urgency_bonus[
            result.urgency
        ]

        result.score = min(
            round(score),
            100,
        )

        return result