from datetime import datetime, UTC

from heshly_core.models.memory import (
    CustomerMemory,
    MemoryItem,
)



class MemoryExpiration:
    """
    Handles expired customer memories.
    """


    def is_expired(
        self,
        memory: MemoryItem,
    ) -> bool:
        """
        Check if a memory has expired.
        """

        if not memory.expires_at:
            return False


        return (
            datetime.now(UTC)
            >
            memory.expires_at
        )



    def remove_expired(
        self,
        customer_memory: CustomerMemory,
    ) -> CustomerMemory:
        """
        Remove expired memories.
        """

        customer_memory.memories = [

            memory

            for memory in customer_memory.memories

            if not self.is_expired(memory)

        ]


        customer_memory.updated_at = datetime.now(UTC)


        return customer_memory



    def active_memories(
        self,
        customer_memory: CustomerMemory,
    ) -> list[MemoryItem]:
        """
        Return only valid memories.
        """

        return [

            memory

            for memory in customer_memory.memories

            if not self.is_expired(memory)

        ]