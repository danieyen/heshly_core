from heshly_core.models.qualification import (
    QualificationResult,
    QualificationStatus,
    UrgencyLevel,
)


class QualificationRules:
    """
    Applies business rules to determine
    customer qualification status.
    """

    def evaluate(
        self,
        result: QualificationResult,
    ) -> QualificationResult:

        # Emergency overrides everything.
        if result.urgency == UrgencyLevel.EMERGENCY:
            result.status = QualificationStatus.ESCALATED

            result.reasons.append(
                "Emergency requires immediate human attention."
            )

            return result

        # Still collecting required information.
        if result.missing_fields:
            result.status = QualificationStatus.COLLECTING_INFO

            result.reasons.append(
                "Required information is incomplete."
            )

            return result

        # Qualification score threshold.
        if result.score >= 80:
            result.status = QualificationStatus.QUALIFIED

            result.reasons.append(
                "Customer meets qualification requirements."
            )
        else:
            result.status = QualificationStatus.NOT_QUALIFIED

            result.reasons.append(
                "Qualification score is below the required threshold."
            )

        return result