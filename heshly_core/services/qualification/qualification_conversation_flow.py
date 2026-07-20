from heshly_core.models.qualification import (
    QualificationAction,
    QualificationResult,
    QualificationStatus,
)

from heshly_core.services.qualification.missing_information_detector import (
    MissingInformationDetector,
)


class QualificationConversationFlow:
    """
    Determines the next conversational action
    after qualification.
    """

    def __init__(
        self,
        detector: MissingInformationDetector | None = None,
    ):
        self.detector = (
            detector
            or MissingInformationDetector()
        )

    def next_step(
        self,
        result: QualificationResult,
    ) -> tuple[
        QualificationAction,
        str | None,
    ]:

        if (
            result.status
            ==
            QualificationStatus.ESCALATED
        ):
            return (
                QualificationAction.ESCALATE,
                None,
            )

        if (
            result.status
            ==
            QualificationStatus.NOT_QUALIFIED
        ):
            return (
                QualificationAction.END_CONVERSATION,
                None,
            )

        if (
            result.status
            ==
            QualificationStatus.COLLECTING_INFO
        ):

            question = self.detector.next_question(
                result
            )

            return (
                QualificationAction.ASK_QUESTION,
                question,
            )

        if (
            result.status
            ==
            QualificationStatus.QUALIFIED
        ):
            return (
                QualificationAction.PROCEED_TO_BOOKING,
                None,
            )

        return (
            QualificationAction.ASK_QUESTION,
            None,
        )