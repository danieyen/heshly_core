from dataclasses import dataclass, field


@dataclass(slots=True)
class CompletenessResult:
    complete: bool
    missing_fields: list[str] = field(default_factory=list)

@dataclass(slots=True)
class RuleResult:
    allowed: bool
    reason: str | None = None

from enum import Enum


class Action(Enum):
    ASK_SERVICE = "ask_service"
    ASK_DATE = "ask_date"
    ASK_TIME = "ask_time"

    CREATE_APPOINTMENT = "create_appointment"

    ESCALATE_HUMAN = "escalate_human"

    ANSWER_QUESTION = "answer_question"

    UNKNOWN = "unknown"


@dataclass(slots=True)
class ActionPlan:
    action: Action
    reason: str