from heshly_core.models.conversation import (
    Conversation,
    ConversationTurn,
)


class MessageHistory:
    """
    Provides convenient access to conversation history.
    """

    def __init__(self, conversation: Conversation):
        self.conversation = conversation

    def all(self) -> list[ConversationTurn]:
        return self.conversation.turns

    def last(self) -> ConversationTurn | None:
        if not self.conversation.turns:
            return None
        return self.conversation.turns[-1]

    def first(self) -> ConversationTurn | None:
        if not self.conversation.turns:
            return None
        return self.conversation.turns[0]

    def count(self) -> int:
        return len(self.conversation.turns)

    def is_empty(self) -> bool:
        return len(self.conversation.turns) == 0

    def clear(self) -> None:
        self.conversation.turns.clear()

    def user_messages(self) -> list[ConversationTurn]:
        return [
            turn
            for turn in self.conversation.turns
            if turn.role.value == "user"
        ]

    def assistant_messages(self) -> list[ConversationTurn]:
        return [
            turn
            for turn in self.conversation.turns
            if turn.role.value == "assistant"
        ]

    def system_messages(self) -> list[ConversationTurn]:
        return [
            turn
            for turn in self.conversation.turns
            if turn.role.value == "system"
        ]