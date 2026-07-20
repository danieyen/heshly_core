from heshly_core.models.guardrail import (
    GuardrailAction,
    GuardrailIssue,
    GuardrailResult,
    GuardrailStatus,
    GuardrailType,
)


class PromptInjectionDetector:
    """
    Detects common prompt injection attempts.
    """

    SUSPICIOUS_PATTERNS = [

        "ignore previous instructions",
        "ignore all previous instructions",

        "forget your instructions",

        "reveal your prompt",
        "show me your prompt",
        "show the system prompt",
        "print the system prompt",

        "you are now",

        "act as",

        "developer message",

        "system prompt",

        "jailbreak",

        "bypass",

        "override",

        "disregard previous",

    ]

    def detect(
        self,
        prompt: str,
    ) -> GuardrailResult:

        result = GuardrailResult()

        text = prompt.lower()

        matches = []

        for pattern in self.SUSPICIOUS_PATTERNS:

            if pattern in text:

                matches.append(pattern)

        if matches:

            result.status = GuardrailStatus.FAILED

            result.action = GuardrailAction.BLOCK

            result.score = 0.0

            for pattern in matches:

                result.issues.append(

                    GuardrailIssue(

                        guardrail_type=GuardrailType.PROMPT_INJECTION,

                        message=f"Detected prompt injection pattern: '{pattern}'",

                        severity="high",

                    )

                )

        return result