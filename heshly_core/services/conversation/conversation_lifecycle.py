from datetime import datetime

from heshly_core.models.conversation import Conversation


class ConversationLifecycle:
    """
    Manages conversation state transitions.
    """

    def start(self, conversation: Conversation) -> Conversation:
        """
        Start a new conversation.
        """

        conversation.status = "active"
        conversation.updated_at = datetime.utcnow()

        return conversation


    def wait(self, conversation: Conversation) -> Conversation:
        """
        Put conversation into waiting state.
        """

        conversation.status = "waiting"
        conversation.updated_at = datetime.utcnow()

        return conversation


    def complete(self, conversation: Conversation) -> Conversation:
        """
        Mark conversation as completed.
        """

        conversation.status = "completed"
        conversation.updated_at = datetime.utcnow()

        return conversation


    def escalate(self, conversation: Conversation) -> Conversation:
        """
        Transfer conversation to human.
        """

        conversation.status = "escalated"
        conversation.updated_at = datetime.utcnow()

        return conversation


    def close(self, conversation: Conversation) -> Conversation:
        """
        Permanently close conversation.
        """

        conversation.status = "closed"
        conversation.updated_at = datetime.utcnow()

        return conversation