from heshly_core.models.guardrail import (
    GuardrailAction,
    GuardrailIssue,
    GuardrailResult,
    GuardrailStatus,
    GuardrailType,
)


class PromptValidator:
    """
    Validates prompts before they are sent to an LLM.
    """

    MAX_PROMPT_LENGTH = 12000
    MIN_PROMPT_LENGTH = 5

    def validate(
        self,
        prompt: str,
    ) -> GuardrailResult:

        result = GuardrailResult()

        prompt = prompt.strip()

        if not prompt:

            result.status = GuardrailStatus.FAILED
            result.action = GuardrailAction.BLOCK
            result.score = 0.0

            result.issues.append(
                GuardrailIssue(
                    guardrail_type=GuardrailType.PROMPT_VALIDATION,
                    message="Prompt is empty.",
                    severity="high",
                )
            )

            return result

        if len(prompt) < self.MIN_PROMPT_LENGTH:

            result.status = GuardrailStatus.WARNING
            result.action = GuardrailAction.REVIEW
            result.score = 0.50

            result.issues.append(
                GuardrailIssue(
                    guardrail_type=GuardrailType.PROMPT_VALIDATION,
                    message="Prompt is unusually short.",
                    severity="low",
                )
            )

        if len(prompt) > self.MAX_PROMPT_LENGTH:

            result.status = GuardrailStatus.FAILED
            result.action = GuardrailAction.BLOCK
            result.score = 0.0

            result.issues.append(
                GuardrailIssue(
                    guardrail_type=GuardrailType.PROMPT_VALIDATION,
                    message="Prompt exceeds maximum length.",
                    severity="high",
                )
            )

        if "    " in prompt:

            if result.status == GuardrailStatus.PASSED:
                result.status = GuardrailStatus.WARNING
                result.action = GuardrailAction.REVIEW
                result.score = 0.90

            result.issues.append(
                GuardrailIssue(
                    guardrail_type=GuardrailType.PROMPT_VALIDATION,
                    message="Prompt contains excessive whitespace.",
                    severity="low",
                )
            )

        return result