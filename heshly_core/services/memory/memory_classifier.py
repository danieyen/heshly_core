from datetime import datetime, timedelta, UTC

from heshly_core.models.memory import (
    MemoryItem,
    MemoryType,
)


class MemoryClassifier:
    """
    Classifies memories based on importance and lifespan.
    """

    def classify(
        self,
        memory: MemoryItem,
    ) -> MemoryItem:
        """
        Apply classification rules.
        """


        # Identity is permanent

        if memory.memory_type == MemoryType.IDENTITY:

            memory.confidence = max(
                memory.confidence,
                0.95,
            )

            memory.expires_at = None



        # Preferences are long-term

        elif memory.memory_type == MemoryType.PREFERENCE:

            memory.expires_at = (
                datetime.now(UTC)
                + timedelta(days=180)
            )



        # Behavior is medium-term

        elif memory.memory_type == MemoryType.BEHAVIOR:

            memory.expires_at = (
                datetime.now(UTC)
                + timedelta(days=90)
            )



        # Temporary memories expire quickly

        elif memory.memory_type == MemoryType.TEMPORARY:

            memory.expires_at = (
                datetime.now(UTC)
                + timedelta(days=7)
            )


        return memory