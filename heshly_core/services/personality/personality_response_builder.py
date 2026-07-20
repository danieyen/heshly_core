from heshly_core.models.personality import (
    PersonalityProfile,
)

from heshly_core.services.personality.tone_engine import (
    ToneEngine,
)

from heshly_core.services.personality.conversation_style_manager import (
    ConversationStyleManager,
)

from heshly_core.services.personality.brand_voice_engine import (
    BrandVoiceEngine,
)


class PersonalityResponseBuilder:
    """
    Combines all personality components
    into a single instruction block that
    can be passed to the Prompt Composer.
    """

    def __init__(self):

        self.tone_engine = ToneEngine()

        self.style_manager = (
            ConversationStyleManager()
        )

        self.brand_voice_engine = (
            BrandVoiceEngine()
        )

    def build(
        self,
        profile: PersonalityProfile,
    ) -> str:

        tone_instruction = (
            self.tone_engine.instruction(
                profile.tone
            )
        )

        style_instruction = (
            self.style_manager.build_instruction(
                style=profile.conversation_style,
                greeting=profile.greeting_style,
                closing=profile.closing_style,
            )
        )

        brand_instruction = (
            self.brand_voice_engine.build_instruction(
                profile.brand_voice
            )
        )

        sections = [
            "Receptionist Personality",
            "",
            "Tone",
            tone_instruction,
            "",
            "Conversation Style",
            style_instruction,
            "",
            "Brand Voice",
            brand_instruction,
        ]

        return "\n".join(sections)