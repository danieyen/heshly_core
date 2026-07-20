from heshly_core.models.memory import (
    CustomerMemory,
)

from heshly_core.services.memory.memory_store import (
    MemoryStore,
)

from heshly_core.services.memory.memory_extractor import (
    MemoryExtractor,
)

from heshly_core.services.memory.memory_classifier import (
    MemoryClassifier,
)



class MemoryManager:
    """
    Main coordinator for customer memory.
    """


    def __init__(
        self,
        store: MemoryStore | None = None,
        extractor: MemoryExtractor | None = None,
        classifier: MemoryClassifier | None = None,
    ):

        self.store = store or MemoryStore()

        self.extractor = (
            extractor
            or MemoryExtractor()
        )

        self.classifier = (
            classifier
            or MemoryClassifier()
        )



    # ------------------------------------------------
    # Remember information from conversation
    # ------------------------------------------------

    def remember(
        self,
        customer_id: str,
        message: str,
    ) -> CustomerMemory:


        memory = self.get_or_create(
            customer_id
        )


        extracted = self.extractor.extract(
            message
        )


        for item in extracted:

            classified = self.classifier.classify(
                item
            )

            memory.add_memory(
                classified
            )


        self.store.save(
            memory
        )


        return memory



    # ------------------------------------------------
    # Retrieve customer memory
    # ------------------------------------------------

    def get(
        self,
        customer_id: str,
    ) -> CustomerMemory | None:

        return self.store.get(
            customer_id
        )



    # ------------------------------------------------
    # Create memory profile
    # ------------------------------------------------

    def get_or_create(
        self,
        customer_id: str,
    ) -> CustomerMemory:


        memory = self.store.get(
            customer_id
        )


        if memory:

            return memory



        return CustomerMemory(
            customer_id=customer_id
        )



    # ------------------------------------------------
    # Forget all customer memory
    # ------------------------------------------------

    def forget(
        self,
        customer_id: str,
    ) -> None:

        self.store.delete(
            customer_id
        )