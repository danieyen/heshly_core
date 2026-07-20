from heshly_core.services.memory.memory_manager import (
    MemoryManager,
)

from heshly_core.services.memory.memory_retriever import (
    MemoryRetriever,
)

from heshly_core.services.memory.memory_ranker import (
    MemoryRanker,
)

from heshly_core.services.memory.customer_profile_builder import (
    CustomerProfileBuilder,
)


class MemoryEngine:
    """
    Main integration layer for customer memory.
    """


    def __init__(
        self,
        manager: MemoryManager | None = None,
        retriever: MemoryRetriever | None = None,
        ranker: MemoryRanker | None = None,
        profile_builder: CustomerProfileBuilder | None = None,
    ):

        self.manager = (
            manager
            or MemoryManager()
        )

        self.retriever = (
            retriever
            or MemoryRetriever(
                self.manager.store
            )
        )

        self.ranker = (
            ranker
            or MemoryRanker()
        )

        self.profile_builder = (
            profile_builder
            or CustomerProfileBuilder()
        )



    def process_message(
        self,
        customer_id: str,
        message: str,
    ):
        """
        Process customer message through memory pipeline.
        """


        # 1. Learn new information

        memory = self.manager.remember(
            customer_id,
            message,
        )


        # 2. Retrieve memories

        memories = self.retriever.get_customer_memory(
            customer_id
        )


        if memories:

            ranked = self.ranker.rank(
                memories.memories
            )

        else:

            ranked = []



        # 3. Build profile

        profile = self.profile_builder.build(
            memory
        )


        return {
            "profile": profile,
            "relevant_memories": ranked,
        }