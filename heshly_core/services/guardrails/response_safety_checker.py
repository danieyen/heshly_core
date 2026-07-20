from heshly_core.models.guardrail import (
    GuardrailAction,
    GuardrailIssue,
    GuardrailResult,
    GuardrailStatus,
    GuardrailType,
)


class ResponseSafetyChecker:
    """
    Checks AI responses for unsafe or prohibited content.
    """

    HIGH_RISK_PATTERNS = [

        "i guarantee",

        "100% guaranteed",

        "you will definitely",

        "stop taking your medication",

        "ignore your doctor",

        "hurt yourself",

        "kill yourself",

        "commit suicide",

        "make a bomb",

    ]

    MEDIUM_RISK_PATTERNS = [

        "legal advice",

        "financial advice",

        "medical advice",

    ]

    def evaluate(
        self,
        response: str,
    ) -> GuardrailResult:

        result = GuardrailResult()

        text = response.lower()

        for phrase in self.HIGH_RISK_PATTERNS:

            if phrase in text:

                result.status = GuardrailStatus.FAILED

                result.action = GuardrailAction.BLOCK

                result.score = 0.0

                result.issues.append(

                    GuardrailIssue(

                        guardrail_type=GuardrailType.RESPONSE_SAFETY,

                        message=f"High-risk content detected: '{phrase}'",

                        severity="high",

                    )

                )

        if result.status == GuardrailStatus.FAILED:
            return result

        for phrase in self.MEDIUM_RISK_PATTERNS:

            if phrase in text:

                result.status = GuardrailStatus.WARNING

                result.action = GuardrailAction.REVIEW

                result.score = 0.50

                result.issues.append(

                    GuardrailIssue(

                        guardrail_type=GuardrailType.RESPONSE_SAFETY,

                        message=f"Potentially sensitive content: '{phrase}'",

                        severity="medium",

                    )

                )

        return result