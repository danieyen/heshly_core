from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y")
    return bool(value)


@dataclass(slots=True)
class ExtractedEntities:
    service: str | None = None
    date: str | None = None
    time: str | None = None
    customer_name: str | None = None
    phone: str | None = None
    email: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Any) -> "ExtractedEntities":
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except Exception:
                return cls()
        if not isinstance(data, dict):
            return cls()
        return cls(
            service=data.get("service"),
            date=data.get("date"),
            time=data.get("time"),
            customer_name=data.get("customer_name") or data.get("customerName"),
            phone=data.get("phone"),
            email=data.get("email"),
            extras=data.get("extras") or {},
        )

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "date": self.date,
            "time": self.time,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email,
            "extras": self.extras,
        }


class Speaker(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

    @classmethod
    def from_value(cls, value: Any) -> "Speaker":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls(value.strip().lower())
            except ValueError:
                return cls.USER
        return cls.USER


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    HANDOVER = "handover"
    CLOSED = "closed"

    @classmethod
    def from_value(cls, value: Any) -> "ConversationStatus":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            # Handle legacy values
            if normalized == "escalated":
                return cls.HANDOVER
            try:
                return cls(normalized)
            except ValueError:
                return cls.ACTIVE
        return cls.ACTIVE


@dataclass(slots=True)
class ConversationTurn:
    role: Speaker
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_dict(cls, data: Any) -> "ConversationTurn":
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except Exception:
                return cls(role=Speaker.USER, message=str(data))
        if not isinstance(data, dict):
            raise ValueError("ConversationTurn data must be dict")
        role = Speaker.from_value(data.get("role"))
        ts = data.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(UTC)
        elif not isinstance(ts, datetime):
            ts = datetime.now(UTC)
        return cls(role=role, message=str(data.get("message") or ""), timestamp=ts)

    def to_dict(self) -> dict:
        return {
            "role": self.role.value if isinstance(self.role, Enum) else str(self.role),
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
        }


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

    @classmethod
    def from_dict(cls, data: Any) -> "Conversation":
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except Exception:
                raise ValueError("Conversation data must be dict")
        if not isinstance(data, dict):
            raise ValueError("Conversation data must be dict")
        status = ConversationStatus.from_value(data.get("status", "active"))
        entities = data.get("entities")
        if isinstance(entities, dict):
            entities = ExtractedEntities.from_dict(entities)
        elif not isinstance(entities, ExtractedEntities):
            entities = ExtractedEntities()
        turns = []
        for t in data.get("turns", []) or []:
            try:
                if isinstance(t, dict):
                    turns.append(ConversationTurn.from_dict(t))
                elif isinstance(t, ConversationTurn):
                    turns.append(t)
            except Exception:
                continue
        created_at = data.get("created_at") or data.get("createdAt")
        updated_at = data.get("updated_at") or data.get("updatedAt")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                created_at = datetime.now(UTC)
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except Exception:
                updated_at = datetime.now(UTC)
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = datetime.now(UTC)
        return cls(
            conversation_id=str(data.get("conversation_id") or data.get("conversationId") or ""),
            customer_id=str(data.get("customer_id") or data.get("customerId") or ""),
            status=status,
            entities=entities,
            turns=turns,
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "entities": self.entities.to_dict() if hasattr(self.entities, "to_dict") else {},
            "turns": [t.to_dict() for t in self.turns],
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else str(self.updated_at),
        }
