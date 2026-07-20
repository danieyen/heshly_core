from heshly_core.models.guardrail import (
    BusinessPolicy,
    EscalationDecision,
    HallucinationEvidence,
)

from heshly_core.services.guardrails.guardrail_manager import (
    GuardrailManager,
)


class GuardrailsEngine:
    """
    Public entry point for all AI guardrail evaluation.

    This engine provides a stable API while delegating the
    underlying work to the GuardrailManager.
    """

    def __init__(
        self,
        manager: GuardrailManager | None = None,
    ):
        self.manager = manager or GuardrailManager()

    def evaluate_prompt(
        self,
        prompt: str,
        policy: BusinessPolicy,
    ) -> EscalationDecision:

        return self.manager.evaluate_prompt(
            prompt,
            policy,
        )

    def evaluate_response(
        self,
        response: str,
        evidence: list[HallucinationEvidence],
    ) -> EscalationDecision:

        return self.manager.evaluate_response(
            response,
            evidence,
        )