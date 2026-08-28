from datetime import datetime, UTC
from typing import Any

from heshly_core.models.conversation import Conversation, ConversationStatus


class ConversationLifecycle:
    """
    Manages conversation state transitions.
    Uses ConversationStatus enum to guarantee contract with
    ConversationManager, persistence, and n8n routing.
    Handles string status from n8n gracefully.
    """

    def _normalize_status(self, status: Any) -> ConversationStatus:
        if isinstance(status, ConversationStatus):
            return status
        if isinstance(status, str):
            return ConversationStatus.from_value(status)
        raise ValueError(f"status must be ConversationStatus or string, got {status}")

    def start(self, conversation: Conversation) -> Conversation:
        """
        Start a new conversation.
        """
        if conversation is None:
            raise ValueError("conversation is required")
        conversation.status = ConversationStatus.ACTIVE
        conversation.updated_at = datetime.now(UTC)
        return conversation

    def wait(self, conversation: Conversation) -> Conversation:
        """
        Put conversation into waiting state (awaiting customer input).
        """
        if conversation is None:
            raise ValueError("conversation is required")
        conversation.status = ConversationStatus.WAITING
        conversation.updated_at = datetime.now(UTC)
        return conversation

    def complete(self, conversation: Conversation) -> Conversation:
        """
        Mark conversation as completed.
        """
        if conversation is None:
            raise ValueError("conversation is required")
        conversation.status = ConversationStatus.COMPLETED
        conversation.updated_at = datetime.now(UTC)
        return conversation

    def escalate(self, conversation: Conversation) -> Conversation:
        """
        Transfer conversation to human (handover).
        """
        if conversation is None:
            raise ValueError("conversation is required")
        conversation.status = ConversationStatus.HANDOVER
        conversation.updated_at = datetime.now(UTC)
        return conversation

    def close(self, conversation: Conversation) -> Conversation:
        """
        Permanently close conversation.
        """
        if conversation is None:
            raise ValueError("conversation is required")
        conversation.status = ConversationStatus.CLOSED
        conversation.updated_at = datetime.now(UTC)
        return conversation

    def transition(self, conversation: Conversation, status: Any) -> Conversation:
        """
        Transition to any status, handling string values from n8n.
        """
        if conversation is None:
            raise ValueError("conversation is required")
        normalized = self._normalize_status(status)
        conversation.status = normalized
        conversation.updated_at = datetime.now(UTC)
        return conversation
