from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass(slots=True)
class ExtractedEntities:
    service: str | None = None
    date: str | None = None
    time: str | None = None
    customer_name: str | None = None
    phone: str | None = None
    email: str | None = None
    extras: dict = field(default_factory=dict)


class Speaker(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    HANDOVER = "handover"
    CLOSED = "closed"


@dataclass(slots=True)
class ConversationTurn:
    role: Speaker
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Conversation:
    conversation_id: str
    customer_id: str

    status: ConversationStatus = ConversationStatus.ACTIVE

    entities: ExtractedEntities = field(default_factory=ExtractedEntities)

    turns: list[ConversationTurn] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

        
    def add_turn(self, turn: ConversationTurn) -> None:
        self.turns.append(turn)
        self.updated_at = datetime.utcnow()

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