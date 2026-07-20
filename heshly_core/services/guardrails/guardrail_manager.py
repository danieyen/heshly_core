from heshly_core.models.guardrail import (
    BusinessPolicy,
    EscalationDecision,
    HallucinationEvidence,
)

from heshly_core.services.guardrails.business_policy_enforcer import (
    BusinessPolicyEnforcer,
)

from heshly_core.services.guardrails.escalation_decision_engine import (
    EscalationDecisionEngine,
)

from heshly_core.services.guardrails.hallucination_detector import (
    HallucinationDetector,
)

from heshly_core.services.guardrails.prompt_injection_detector import (
    PromptInjectionDetector,
)

from heshly_core.services.guardrails.prompt_validator import (
    PromptValidator,
)

from heshly_core.services.guardrails.response_safety_checker import (
    ResponseSafetyChecker,
)

from heshly_core.services.guardrails.sensitive_data_protector import (
    SensitiveDataProtector,
)


class GuardrailManager:
    """
    Coordinates all AI guardrail services.
    """

    def __init__(self):

        self.prompt_validator = PromptValidator()

        self.prompt_injection = PromptInjectionDetector()

        self.sensitive_data = SensitiveDataProtector()

        self.business_policy = BusinessPolicyEnforcer()

        self.response_safety = ResponseSafetyChecker()

        self.hallucination = HallucinationDetector()

        self.escalation = EscalationDecisionEngine()

    def evaluate_prompt(
        self,
        prompt: str,
        policy: BusinessPolicy,
    ) -> EscalationDecision:

        results = [

            self.prompt_validator.validate(
                prompt
            ),

            self.prompt_injection.detect(
                prompt
            ),

            self.sensitive_data.detect(
                prompt
            ),

            self.business_policy.evaluate(
                prompt,
                policy,
            ),

        ]

        return self.escalation.decide(
            results
        )

    def evaluate_response(
        self,
        response: str,
        evidence: list[HallucinationEvidence],
    ) -> EscalationDecision:

        results = [

            self.response_safety.evaluate(
                response
            ),

            self.hallucination.evaluate(
                response,
                evidence,
            ),

            self.sensitive_data.detect(
                response
            ),

        ]

        return self.escalation.decide(
            results
        )