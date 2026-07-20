from heshly_core.models.personality import (
    PersonalityProfile,
)


class MultiLanguagePersonality:
    """
    Builds language instructions while
    preserving the receptionist personality.
    """

    def build_instruction(
        self,
        profile: PersonalityProfile,
    ) -> str:

        language = profile.language

        return (
            f"Respond in {language.language_name} "
            f"({language.language_code}). "
            f"Maintain the configured receptionist "
            f"personality, tone, style and brand voice. "
            f"Locale: {language.locale}."
        )