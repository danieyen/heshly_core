from heshly_core.models.guardrail import (
    GuardrailAction,
    GuardrailIssue,
    GuardrailResult,
    GuardrailStatus,
    GuardrailType,
    HallucinationEvidence,
)


class HallucinationDetector:
    """
    Framework for evaluating confidence in AI responses.
    """

    def evaluate(
        self,
        response: str,
        evidence: list[HallucinationEvidence],
    ) -> GuardrailResult:

        result = GuardrailResult()

        if not evidence:
            result.status = GuardrailStatus.WARNING
            result.action = GuardrailAction.REVIEW
            result.score = 0.50

            result.issues.append(
                GuardrailIssue(
                    guardrail_type=GuardrailType.HALLUCINATION,
                    message="No supporting evidence provided.",
                    severity="medium",
                )
            )

            return result

        average = sum(
            item.confidence
            for item in evidence
        ) / len(evidence)

        failed = [
            item
            for item in evidence
            if not item.passed
        ]

        result.score = round(average, 2)

        if failed:

            result.status = GuardrailStatus.WARNING
            result.action = GuardrailAction.REVIEW

            for item in failed:

                result.issues.append(
                    GuardrailIssue(
                        guardrail_type=GuardrailType.HALLUCINATION,
                        message=item.message,
                        severity="medium",
                    )
                )

        return result