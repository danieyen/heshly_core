from heshly_core.models.conversation import (
    Conversation,
    Speaker,
)


class ConversationPromptBuilder:
    """
    Builds the conversation portion of the AI prompt.
    """

    ROLE_NAMES = {
        Speaker.USER: "User",
        Speaker.ASSISTANT: "Assistant",
        Speaker.SYSTEM: "System",
    }

    def build(
        self,
        conversation: Conversation,
    ) -> str:

        lines = [
            "Conversation History:",
            "",
        ]

        for turn in conversation.turns:

            role = self.ROLE_NAMES.get(
                turn.role,
                "Unknown",
            )

            lines.append(
                f"{role}: {turn.message}"
            )

            lines.append("")

        return "\n".join(lines).rstrip()