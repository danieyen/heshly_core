from dataclasses import dataclass, field
from enum import Enum


@dataclass(slots=True)
class CompletenessResult:
    complete: bool
    missing_fields: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return self.complete and not self.missing_fields


@dataclass(slots=True)
class RuleResult:
    allowed: bool
    reason: str | None = None

    @property
    def is_allowed(self) -> bool:
        return bool(self.allowed)


class Action(Enum):
    ASK_SERVICE = "ask_service"
    ASK_DATE = "ask_date"
    ASK_TIME = "ask_time"
    ASK_INFORMATION = "ask_information"
    PRESENT_OPTIONS = "present_options"
    CREATE_APPOINTMENT = "create_appointment"
    CONFIRM_BOOKING = "confirm_booking"
    ESCALATE_HUMAN = "escalate_human"
    ANSWER_QUESTION = "answer_question"
    END_CONVERSATION = "end_conversation"
    UNKNOWN = "unknown"

    @property
    def requires_availability(self) -> bool:
        return self in (Action.PRESENT_OPTIONS, Action.CREATE_APPOINTMENT, Action.CONFIRM_BOOKING)

    @property
    def is_booking_action(self) -> bool:
        return self in (Action.CREATE_APPOINTMENT, Action.CONFIRM_BOOKING)


@dataclass(slots=True)
class ActionPlan:
    action: Action
    reason: str

    def to_dict(self) -> dict:
        return {
            "action": self.action.value if isinstance(self.action, Enum) else str(self.action),
            "reason": self.reason,
        }
