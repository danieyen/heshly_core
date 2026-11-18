from dataclasses import dataclass, field

from heshly_core.models.conversation import ExtractedEntities
from heshly_core.models.intent import IntentResult
from heshly_core.models.qualification import (
    QualificationAction,
    QualificationResult,
)
from heshly_core.models.workflow import (
    ActionPlan,
    CompletenessResult,
    RuleResult,
)


@dataclass(slots=True)
class DecisionContext:
    """
    Shared context flowing through the Decision Engine.
    Every component enriches this object.
    """

    raw_message: str

    intent: IntentResult | None = None
    entities: ExtractedEntities | None = None

    # Existing booking pipeline
    completeness: CompletenessResult | None = None
    rules: RuleResult | None = None
    action: ActionPlan | None = None

    # Lead/customer qualification pipeline
    qualification: QualificationResult | None = None
    qualification_action: QualificationAction | None = None
    qualification_response: str | None = None

    metadata: dict = field(default_factory=dict)
