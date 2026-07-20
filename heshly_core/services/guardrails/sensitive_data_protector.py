import re

from heshly_core.models.guardrail import (
    GuardrailAction,
    GuardrailIssue,
    GuardrailResult,
    GuardrailStatus,
    GuardrailType,
)


class SensitiveDataProtector:
    """
    Detects common sensitive information in prompts and responses.
    """

    PATTERNS = [

        (
            "API Key",

            re.compile(
                r"\b(sk-[A-Za-z0-9_\-]{20,})\b"
            ),

            "high",
        ),

        (
            "Bearer Token",

            re.compile(
                r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
                re.IGNORECASE,
            ),

            "high",
        ),

        (
            "JWT",

            re.compile(
                r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"
            ),

            "high",
        ),

        (
            "Private Key",

            re.compile(
                r"-----BEGIN .* PRIVATE KEY-----"
            ),

            "high",
        ),

        (
            "Password",

            re.compile(
                r"password\s*[:=]\s*\S+",
                re.IGNORECASE,
            ),

            "high",
        ),

        (
            "Credit Card",

            re.compile(
                r"\b(?:\d[ -]*?){13,19}\b"
            ),

            "medium",
        ),

        (
            "Email Address",

            re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ),

            "low",
        ),

        (
            "Phone Number",

            re.compile(
                r"\+?\d[\d\s()-]{7,}\d"
            ),

            "low",
        ),
    ]

    def detect(
        self,
        text: str,
    ) -> GuardrailResult:

        result = GuardrailResult()

        highest = "none"

        severity_order = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
        }

        for label, pattern, severity in self.PATTERNS:

            if pattern.search(text):

                result.issues.append(

                    GuardrailIssue(

                        guardrail_type=GuardrailType.SENSITIVE_DATA,

                        message=f"{label} detected.",

                        severity=severity,

                    )

                )

                if severity_order[severity] > severity_order[highest]:
                    highest = severity

        if highest == "high":

            result.status = GuardrailStatus.FAILED
            result.action = GuardrailAction.BLOCK
            result.score = 0.0

        elif highest == "medium":

            result.status = GuardrailStatus.WARNING
            result.action = GuardrailAction.REVIEW
            result.score = 0.5

        elif highest == "low":

            result.status = GuardrailStatus.WARNING
            result.action = GuardrailAction.REVIEW
            result.score = 0.9

        return result