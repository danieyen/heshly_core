from heshly_core.models.knowledge import KnowledgeContext

from .knowledge_engine import KnowledgeEngine


class KnowledgeCache:
    """
    Simple in-memory cache for business knowledge.

    Later this can be replaced with Redis or another distributed cache.
    """

    _cache: dict[str, KnowledgeEngine] = {}

    @classmethod
    def get(cls, business_id: str) -> KnowledgeEngine | None:
        return cls._cache.get(business_id)

    @classmethod
    def set(
        cls,
        business_id: str,
        context: KnowledgeContext,
    ) -> KnowledgeEngine:
        engine = KnowledgeEngine(context)
        cls._cache[business_id] = engine
        return engine

    @classmethod
    def clear(cls):
        cls._cache.clear()

    @classmethod
    def remove(cls, business_id: str):
        cls._cache.pop(business_id, None)

    @classmethod
    def size(cls) -> int:
        return len(cls._cache)