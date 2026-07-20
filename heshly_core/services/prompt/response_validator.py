from heshly_core.models.prompt import (
    PromptResponse,
    ValidationResult,
)


class ResponseValidator:
    """
    Validates AI responses before delivery.
    """

    MAX_LENGTH = 2000

    FORBIDDEN_PHRASES = [
        "I guarantee",
        "I promise",
    ]

    MIN_CONFIDENCE = 0.50

    def validate(
        self,
        response: PromptResponse,
    ) -> ValidationResult:

        result = ValidationResult()

        message = response.message.strip()

        if not message:

            result.valid = False

            result.errors.append(
                "Response is empty."
            )

        if len(message) > self.MAX_LENGTH:

            result.valid = False

            result.errors.append(
                "Response exceeds maximum length."
            )

        message_lower = message.lower()

        for phrase in self.FORBIDDEN_PHRASES:

            if phrase.lower() in message_lower:

                result.valid = False

                result.errors.append(
                    f"Forbidden phrase detected: '{phrase}'"
                )

        if response.confidence < self.MIN_CONFIDENCE:

            result.valid = False

            result.errors.append(
                "Confidence below acceptable threshold."
            )

        return result