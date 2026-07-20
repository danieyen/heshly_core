from heshly_core.models.prompt import (
    PromptResponse,
    ResponseType,
)


class ResponseGenerator:
    """
    Generates AI responses.

    For now this uses a mock implementation.
    Later it will call an LLM provider.
    """

    def generate(
        self,
        prompt: str,
    ) -> PromptResponse:

        prompt_lower = prompt.lower()

        if "appointment" in prompt_lower:

            message = (
                "I'd be happy to help you book an appointment. "
                "Which day works best for you?"
            )

        elif "price" in prompt_lower:

            message = (
                "I'd be happy to help with pricing information."
            )

        elif "hello" in prompt_lower:

            message = (
                "Hello! How may I assist you today?"
            )

        else:

            message = (
                "Could you please tell me a little more?"
            )

        return PromptResponse(
            message=message,
            response_type=ResponseType.TEXT,
            confidence=1.0,
        )