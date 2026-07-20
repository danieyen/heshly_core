from heshly_core.models.personality import (
    PersonalityProfile,
)

from heshly_core.services.personality.personality_validator import (
    PersonalityValidator,
)

from heshly_core.services.personality.personality_response_builder import (
    PersonalityResponseBuilder,
)

from heshly_core.services.personality.multi_language_personality import (
    MultiLanguagePersonality,
)


class PersonalityConversationFlow:
    """
    Coordinates all receptionist personality
    components for prompt generation.
    """

    def __init__(self):

        self.validator = (
            PersonalityValidator()
        )

        self.response_builder = (
            PersonalityResponseBuilder()
        )

        self.language_engine = (
            MultiLanguagePersonality()
        )

    def execute(
        self,
        profile: PersonalityProfile,
    ) -> dict:

        validation = self.validator.validate(
            profile
        )

        if not validation.valid:

            return {
                "success": False,
                "validation": validation,
                "personality": None,
            }

        personality_instruction = (
            self.response_builder.build(
                profile
            )
        )

        language_instruction = (
            self.language_engine.build_instruction(
                profile
            )
        )

        return {
            "success": True,
            "validation": validation,
            "personality": personality_instruction,
            "language": language_instruction,
        }