from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(slots=True)
class CompletenessResult:
    complete: bool
    missing_fields: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.complete, bool):
            raise ValueError("complete must be a boolean")
        if not isinstance(self.missing_fields, list):
            raise ValueError("missing_fields must be a list")
        # Normalize missing_fields to stripped strings
        normalized: list[str] = []
        for f in self.missing_fields:
            if isinstance(f, str) and f.strip():
                normalized.append(f.strip())
        object.__setattr__(self, "missing_fields", normalized)
        # Enforce consistency: if missing_fields present, complete must be False
        if normalized and self.complete:
            object.__setattr__(self, "complete", False)

    @property
    def is_complete(self) -> bool:
        return self.complete and not self.missing_fields

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "missing_fields": list(self.missing_fields),
            "is_complete": self.is_complete,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "CompletenessResult":
        if not isinstance(data, dict):
            raise ValueError("CompletenessResult data must be a dict")
        return cls(
            complete=bool(data.get("complete", False)),
            missing_fields=list(data.get("missing_fields", [])),
        )


@dataclass(slots=True)
class RuleResult:
    allowed: bool
    reason: str | None = None

    def __post_init__(self):
        if not isinstance(self.allowed, bool):
            # Coerce truthy values but enforce bool storage
            object.__setattr__(self, "allowed", bool(self.allowed))
        if self.reason is not None and not isinstance(self.reason, str):
            raise ValueError("reason must be a string or None")
        if isinstance(self.reason, str):
            stripped = self.reason.strip()
            object.__setattr__(self, "reason", stripped if stripped else None)

    @property
    def is_allowed(self) -> bool:
        return bool(self.allowed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "is_allowed": self.is_allowed,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "RuleResult":
        if not isinstance(data, dict):
            raise ValueError("RuleResult data must be a dict")
        return cls(
            allowed=bool(data.get("allowed", False)),
            reason=data.get("reason"),
        )


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

    @classmethod
    def from_value(cls, value: Any) -> "Action":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            for member in cls:
                if member.value == normalized:
                    return member
        return cls.UNKNOWN

    @property
    def requires_availability(self) -> bool:
        return self in (Action.PRESENT_OPTIONS, Action.CREATE_APPOINTMENT, Action.CONFIRM_BOOKING)

    @property
    def is_booking_action(self) -> bool:
        return self in (Action.CREATE_APPOINTMENT, Action.CONFIRM_BOOKING)

    @property
    def is_terminal(self) -> bool:
        return self in (Action.END_CONVERSATION, Action.ESCALATE_HUMAN)


@dataclass(slots=True)
class ActionPlan:
    action: Action
    reason: str

    def __post_init__(self):
        if isinstance(self.action, str):
            object.__setattr__(self, "action", Action.from_value(self.action))
        if not isinstance(self.action, Action):
            raise ValueError("action must be an Action enum")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        object.__setattr__(self, "reason", self.reason.strip())

    def to_dict(self) -> dict:
        return {
            "action": self.action.value if isinstance(self.action, Enum) else str(self.action),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "ActionPlan":
        if not isinstance(data, dict):
            raise ValueError("ActionPlan data must be a dict")
        action_val = data.get("action", Action.UNKNOWN)
        return cls(
            action=Action.from_value(action_val),
            reason=str(data.get("reason", "")).strip() or "no reason provided",
        )
