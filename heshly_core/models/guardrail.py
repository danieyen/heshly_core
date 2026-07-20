from dataclasses import dataclass, field
from enum import Enum


class GuardrailStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class GuardrailAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"
    ESCALATE = "escalate"


class GuardrailType(str, Enum):
    PROMPT_VALIDATION = "prompt_validation"
    PROMPT_INJECTION = "prompt_injection"
    SENSITIVE_DATA = "sensitive_data"
    BUSINESS_POLICY = "business_policy"
    RESPONSE_SAFETY = "response_safety"
    HALLUCINATION = "hallucination"


@dataclass(slots=True)
class GuardrailIssue:
    guardrail_type: GuardrailType
    message: str
    severity: str = "medium"


@dataclass(slots=True)
class BusinessPolicy:
    prohibited_phrases: list[str] = field(default_factory=list)
    escalation_keywords: list[str] = field(default_factory=list)
    require_human_review: bool = False


@dataclass(slots=True)
class HallucinationEvidence:
    source: str
    passed: bool
    confidence: float
    message: str


@dataclass(slots=True)
class EscalationDecision:
    """
    Final decision after evaluating all guardrails.
    """

    action: GuardrailAction = GuardrailAction.ALLOW

    reason: str = "No escalation required."


@dataclass(slots=True)
class GuardrailResult:
    status: GuardrailStatus = GuardrailStatus.PASSED
    action: GuardrailAction = GuardrailAction.ALLOW
    issues: list[GuardrailIssue] = field(default_factory=list)
    score: float = 1.0
    metadata: dict[str, str] = field(default_factory=dict)