from heshly_core.models.guardrail import (
    EscalationDecision,
    GuardrailAction,
    GuardrailResult,
)


class EscalationDecisionEngine:
    """
    Determines the final action after all guardrail checks.
    """

    def decide(
        self,
        results: list[GuardrailResult],
    ) -> EscalationDecision:

        for result in results:

            if result.action == GuardrailAction.BLOCK:

                return EscalationDecision(
                    action=GuardrailAction.BLOCK,
                    reason="Blocked by AI guardrails.",
                )

        for result in results:

            if result.action == GuardrailAction.ESCALATE:

                return EscalationDecision(
                    action=GuardrailAction.ESCALATE,
                    reason="Escalation required.",
                )

        for result in results:

            if result.action == GuardrailAction.REVIEW:

                return EscalationDecision(
                    action=GuardrailAction.REVIEW,
                    reason="Human review required.",
                )

        return EscalationDecision()