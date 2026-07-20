from heshly_core.models.conversation import Conversation

from heshly_core.services.conversation.context_builder import ContextBuilder
from heshly_core.services.conversation.conversation_manager import ConversationManager
from heshly_core.services.conversation.message_history import MessageHistory


class ConversationEngine:
    """
    Coordinates conversation management services.
    """

    def __init__(self):
        self.manager = ConversationManager()

    def create(
        self,
        conversation_id: str,
        customer_id: str,
    ) -> Conversation:
        return self.manager.create(
            conversation_id=conversation_id,
            customer_id=customer_id,
        )

    def context(self, conversation: Conversation) -> dict:
        return ContextBuilder(conversation).build()

    def history(self, conversation: Conversation) -> MessageHistory:
        return MessageHistory(conversation)

    def save(self, conversation: Conversation) -> None:
        self.manager.save(conversation)

    def get(self, conversation_id: str) -> Conversation | None:
        return self.manager.get(conversation_id)

    def delete(self, conversation_id: str) -> None:
        self.manager.delete(conversation_id)