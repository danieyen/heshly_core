from heshly_core.models.conversation import Conversation


class ConversationCache:
    """
    Simple in-memory cache for active conversations.
    """

    def __init__(self):
        self._cache: dict[str, Conversation] = {}

    def put(self, conversation: Conversation) -> None:
        self._cache[conversation.conversation_id] = conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self._cache.get(conversation_id)

    def exists(self, conversation_id: str) -> bool:
        return conversation_id in self._cache

    def remove(self, conversation_id: str) -> None:
        self._cache.pop(conversation_id, None)

    def clear(self) -> None:
        self._cache.clear()

    def count(self) -> int:
        return len(self._cache)

    def all(self) -> list[Conversation]:
        return list(self._cache.values())