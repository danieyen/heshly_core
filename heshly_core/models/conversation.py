from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


@dataclass(slots=True)
class ExtractedEntities:
    service: str | None = None
    date: str | None = None
    time: str | None = None
    customer_name: str | None = None
    phone: str | None = None
    email: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


class Speaker(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    HANDOVER = "handover"
    CLOSED = "closed"


@dataclass(slots=True)
class ConversationTurn:
    role: Speaker
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Conversation:
    conversation_id: str
    customer_id: str

    status: ConversationStatus = ConversationStatus.ACTIVE

    entities: ExtractedEntities = field(default_factory=ExtractedEntities)

    turns: list[ConversationTurn] = field(default_factory=list)

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_turn(self, turn: ConversationTurn) -> None:
        self.turns.append(turn)
        self.updated_at = datetime.now(UTC)

    def last_turn(self) -> ConversationTurn | None:
        if not self.turns:
            return None
        return self.turns[-1]

    def last_message(self) -> str | None:
        last = self.last_turn()
        return last.message if last else None

    def turn_count(self) -> int:
        return len(self.turns)

    def is_active(self) -> bool:
        return self.status == ConversationStatus.ACTIVE

    def is_waiting(self) -> bool:
        return self.status == ConversationStatus.WAITING

    def is_handover(self) -> bool:
        return self.status == ConversationStatus.HANDOVER

    def is_closed(self) -> bool:
        return self.status in (ConversationStatus.CLOSED, ConversationStatus.COMPLETED)

    def is_terminal(self) -> bool:
        return self.status in (ConversationStatus.COMPLETED, ConversationStatus.CLOSED, ConversationStatus.HANDOVER)
