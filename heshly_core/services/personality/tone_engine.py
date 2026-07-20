from heshly_core.models.personality import (
    PersonalityTone,
)


class ToneEngine:
    """
    Applies personality tone instructions
    to AI responses.
    """

    _TONE_INSTRUCTIONS = {
        PersonalityTone.FRIENDLY: (
            "Use a warm, welcoming and approachable tone."
        ),

        PersonalityTone.PROFESSIONAL: (
            "Use a professional, courteous and confident tone."
        ),

        PersonalityTone.FORMAL: (
            "Use a formal, respectful and precise tone."
        ),

        PersonalityTone.CASUAL: (
            "Use a relaxed, conversational tone."
        ),

        PersonalityTone.EMPATHETIC: (
            "Show empathy, reassurance and understanding."
        ),

        PersonalityTone.LUXURY: (
            "Use an elegant, premium and refined tone."
        ),
    }

    def instruction(
        self,
        tone: PersonalityTone,
    ) -> str:
        """
        Returns the instruction associated
        with the selected tone.
        """

        return self._TONE_INSTRUCTIONS.get(
            tone,
            self._TONE_INSTRUCTIONS[
                PersonalityTone.PROFESSIONAL
            ],
        )

    def apply(
        self,
        *,
        response: str,
        tone: PersonalityTone,
    ) -> str:
        """
        Wraps the response with the selected
        tone instruction for downstream prompt
        composition.
        """

        instruction = self.instruction(
            tone
        )

        return (
            f"{instruction}\n\n"
            f"Response:\n{response}"
        )