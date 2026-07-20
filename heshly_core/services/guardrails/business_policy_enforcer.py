from heshly_core.models.guardrail import (
    BusinessPolicy,
    GuardrailAction,
    GuardrailIssue,
    GuardrailResult,
    GuardrailStatus,
    GuardrailType,
)


class BusinessPolicyEnforcer:
    """
    Enforces tenant-specific business policies.
    """

    def evaluate(
        self,
        text: str,
        policy: BusinessPolicy,
    ) -> GuardrailResult:

        result = GuardrailResult()

        lower = text.lower()

        for phrase in policy.prohibited_phrases:

            if phrase.lower() in lower:

                result.status = GuardrailStatus.FAILED
                result.action = GuardrailAction.BLOCK
                result.score = 0.0

                result.issues.append(

                    GuardrailIssue(

                        guardrail_type=GuardrailType.BUSINESS_POLICY,

                        message=f"Prohibited phrase detected: '{phrase}'",

                        severity="high",

                    )

                )

        for keyword in policy.escalation_keywords:

            if keyword.lower() in lower:

                result.status = GuardrailStatus.WARNING
                result.action = GuardrailAction.ESCALATE

                if result.score > 0.5:
                    result.score = 0.5

                result.issues.append(

                    GuardrailIssue(

                        guardrail_type=GuardrailType.BUSINESS_POLICY,

                        message=f"Escalation keyword detected: '{keyword}'",

                        severity="medium",

                    )

                )

        if (
            policy.require_human_review
            and result.status == GuardrailStatus.PASSED
        ):

            result.status = GuardrailStatus.WARNING
            result.action = GuardrailAction.REVIEW
            result.score = 0.8

            result.issues.append(

                GuardrailIssue(

                    guardrail_type=GuardrailType.BUSINESS_POLICY,

                    message="Human review required by business policy.",

                    severity="low",

                )

            )

        return result