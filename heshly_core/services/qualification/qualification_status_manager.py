from heshly_core.models.qualification import (
    QualificationResult,
    QualificationStatus,
    UrgencyLevel,
)


class QualificationStatusManager:
    """
    Determines the qualification lifecycle state.
    """

    QUALIFICATION_THRESHOLD = 80

    def update(
        self,
        result: QualificationResult,
    ) -> QualificationResult:

        # Emergency overrides everything.
        if result.urgency == UrgencyLevel.EMERGENCY:
            result.status = QualificationStatus.ESCALATED
            return result

        # Customer cannot proceed.
        if not result.eligible:
            result.status = QualificationStatus.NOT_QUALIFIED
            return result

        # Still collecting information.
        if result.missing_fields:
            result.status = (
                QualificationStatus.COLLECTING_INFO
            )
            return result

        # Ready to proceed.
        if (
            result.score
            >= self.QUALIFICATION_THRESHOLD
        ):
            result.status = (
                QualificationStatus.QUALIFIED
            )
        else:
            result.status = (
                QualificationStatus.NOT_QUALIFIED
            )

        return result