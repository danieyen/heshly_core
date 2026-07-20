from heshly_core.models.conversation import Conversation


class ConversationStore:
    """
    Simple in-memory conversation store.

    Later this will be replaced by ERPNext persistence.
    """

    def __init__(self):
        self._store: dict[str, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._store[conversation.conversation_id] = conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return self._store.get(conversation_id)

    def exists(self, conversation_id: str) -> bool:
        return conversation_id in self._store

    def delete(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)

    def all(self) -> list[Conversation]:
        return list(self._store.values())

    def count(self) -> int:
        return len(self._store)