from heshly_core.models.personality import (
    ConversationStyle,
    GreetingStyle,
    ClosingStyle,
)


class ConversationStyleManager:
    """
    Builds conversation style instructions
    for prompt composition.
    """

    _STYLE_INSTRUCTIONS = {
        ConversationStyle.SHORT: (
            "Keep responses concise and to the point."
        ),
        ConversationStyle.BALANCED: (
            "Provide enough detail while remaining concise."
        ),
        ConversationStyle.DETAILED: (
            "Provide complete explanations with sufficient detail."
        ),
    }

    _GREETING_INSTRUCTIONS = {
        GreetingStyle.NONE: (
            "Do not include a greeting."
        ),
        GreetingStyle.SIMPLE: (
            "Begin with a simple greeting."
        ),
        GreetingStyle.WARM: (
            "Begin with a warm and welcoming greeting."
        ),
        GreetingStyle.ENTHUSIASTIC: (
            "Begin with an enthusiastic greeting."
        ),
    }

    _CLOSING_INSTRUCTIONS = {
        ClosingStyle.NONE: (
            "Do not include a closing."
        ),
        ClosingStyle.SIMPLE: (
            "End with a simple closing."
        ),
        ClosingStyle.FRIENDLY: (
            "End with a friendly closing."
        ),
        ClosingStyle.PROFESSIONAL: (
            "End with a professional closing."
        ),
    }

    def build_instruction(
        self,
        *,
        style: ConversationStyle,
        greeting: GreetingStyle,
        closing: ClosingStyle,
    ) -> str:
        """
        Returns a complete conversation
        style instruction.
        """

        instructions = [
            self._STYLE_INSTRUCTIONS[style],
            self._GREETING_INSTRUCTIONS[greeting],
            self._CLOSING_INSTRUCTIONS[closing],
        ]

        return " ".join(instructions)