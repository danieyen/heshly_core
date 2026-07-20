from datetime import datetime, timedelta, UTC

from heshly_core.models.conversation import Conversation


class ConversationRecovery:
    """
    Handles recovering interrupted conversations.
    """

    def __init__(self, timeout_hours: int = 24):
        self.timeout = timedelta(hours=timeout_hours)


    def is_stale(self, conversation: Conversation) -> bool:
        """
        Check if conversation has been inactive too long.
        """

        if not conversation.updated_at:
            return False

        return datetime.now(UTC) - conversation.updated_at > self.timeout


    def recover(self, conversation: Conversation) -> Conversation:
        """
        Recover an interrupted conversation.
        """

        conversation.status = "active"
        conversation.updated_at = datetime.now(UTC)

        return conversation


    def expire(self, conversation: Conversation) -> Conversation:
        """
        Mark abandoned conversation as expired.
        """

        conversation.status = "expired"
        conversation.updated_at = datetime.now(UTC)

        return conversation


    def needs_recovery(self, conversation: Conversation) -> bool:
        """
        Determine whether recovery is required.
        """

        return (
            conversation.status in [
                "active",
                "waiting"
            ]
            and self.is_stale(conversation)
        )