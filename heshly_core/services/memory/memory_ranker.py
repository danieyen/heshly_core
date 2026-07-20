from datetime import datetime, UTC

from heshly_core.models.memory import (
    MemoryItem,
    MemoryType,
)


class MemoryRanker:
    """
    Ranks memories by usefulness.
    """


    def rank(
        self,
        memories: list[MemoryItem],
        limit: int = 5,
    ) -> list[MemoryItem]:

        scored = []


        for memory in memories:

            score = self.calculate_score(
                memory
            )

            scored.append(
                (
                    score,
                    memory
                )
            )


        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )


        return [
            item[1]
            for item in scored[:limit]
        ]



    def calculate_score(
        self,
        memory: MemoryItem,
    ) -> float:

        confidence_score = (
            memory.confidence * 0.5
        )


        recency_score = self.recency_score(
            memory
        ) * 0.3


        type_score = (
            self.type_importance(
                memory.memory_type
            )
            * 0.2
        )


        return (
            confidence_score
            +
            recency_score
            +
            type_score
        )



    def recency_score(
        self,
        memory: MemoryItem,
    ) -> float:

        age = (
            datetime.now(UTC)
            -
            memory.updated_at
        ).days


        if age <= 7:
            return 1.0


        if age <= 30:
            return 0.7


        if age <= 180:
            return 0.4


        return 0.1



    def type_importance(
        self,
        memory_type: MemoryType,
    ) -> float:

        importance = {

            MemoryType.IDENTITY: 1.0,

            MemoryType.PREFERENCE: 0.9,

            MemoryType.HISTORY: 0.8,

            MemoryType.BEHAVIOR: 0.6,

            MemoryType.TEMPORARY: 0.3,

        }


        return importance.get(
            memory_type,
            0.5,
        )