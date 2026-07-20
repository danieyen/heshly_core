from heshly_core.models.memory import (
    MemoryType,
    CustomerMemory,
)

from heshly_core.services.memory.memory_store import (
    MemoryStore,
)



class MemoryRetriever:
    """
    Retrieves relevant customer memories.
    """


    def __init__(
        self,
        store: MemoryStore | None = None,
    ):

        self.store = store or MemoryStore()



    def get_customer_memory(
        self,
        customer_id: str,
    ) -> CustomerMemory | None:
        """
        Retrieve complete customer memory profile.
        """

        return self.store.get(
            customer_id
        )



    def retrieve_by_type(
        self,
        customer_id: str,
        memory_type: MemoryType,
    ):
        """
        Retrieve memories by category.
        """

        memory = self.get_customer_memory(
            customer_id
        )


        if not memory:
            return []



        return memory.get_memories_by_type(
            memory_type
        )



    def search(
        self,
        customer_id: str,
        keyword: str,
    ):
        """
        Simple keyword memory search.
        """

        memory = self.get_customer_memory(
            customer_id
        )


        if not memory:
            return []


        keyword = keyword.lower()


        results = []


        for item in memory.memories:

            if (
                keyword in item.key.lower()
                or
                keyword in item.value.lower()
            ):

                results.append(item)


        return results