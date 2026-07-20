from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum


class MemoryType(str, Enum):
    """
    Categories of customer memory.
    """

    IDENTITY = "identity"

    PREFERENCE = "preference"

    BEHAVIOR = "behavior"

    HISTORY = "history"

    TEMPORARY = "temporary"



@dataclass(slots=True)
class MemoryItem:
    """
    Single piece of customer memory.
    """

    key: str
    value: str

    memory_type: MemoryType

    confidence: float = 1.0

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    expires_at: datetime | None = None



@dataclass(slots=True)
class CustomerMemory:
    """
    Complete memory profile for a customer.
    """

    customer_id: str

    memories: list[MemoryItem] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    def add_memory(
        self,
        memory: MemoryItem,
    ) -> None:

        self.memories.append(memory)

        self.updated_at = datetime.now(UTC)



    def get_memories_by_type(
        self,
        memory_type: MemoryType,
    ) -> list[MemoryItem]:

        return [
            memory
            for memory in self.memories
            if memory.memory_type == memory_type
        ]