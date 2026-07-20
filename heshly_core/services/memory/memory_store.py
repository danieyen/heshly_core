from heshly_core.models.memory import CustomerMemory


class MemoryStore:
    """
    Temporary in-memory storage for customer memories.

    Future:
    Replace with ERPNext database storage.
    """


    def __init__(self):
        self._memory: dict[str, CustomerMemory] = {}


    def save(
        self,
        memory: CustomerMemory,
    ) -> None:
        """
        Save customer memory.
        """

        self._memory[memory.customer_id] = memory



    def get(
        self,
        customer_id: str,
    ) -> CustomerMemory | None:
        """
        Retrieve customer memory.
        """

        return self._memory.get(customer_id)



    def exists(
        self,
        customer_id: str,
    ) -> bool:
        """
        Check if memory exists.
        """

        return customer_id in self._memory



    def delete(
        self,
        customer_id: str,
    ) -> None:
        """
        Delete customer memory.
        """

        self._memory.pop(
            customer_id,
            None,
        )



    def count(self) -> int:
        """
        Number of stored customer memories.
        """

        return len(self._memory)



    def all(self) -> list[CustomerMemory]:
        """
        Return all customer memories.
        """

        return list(
            self._memory.values()
        )