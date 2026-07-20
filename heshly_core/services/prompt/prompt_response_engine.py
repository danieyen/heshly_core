from heshly_core.models.prompt import (
    PromptRequest,
    PromptResponse,
    ResponseChannel,
)

from heshly_core.services.prompt.prompt_composer import (
    PromptComposer,
)

from heshly_core.services.prompt.response_generator import (
    ResponseGenerator,
)

from heshly_core.services.prompt.response_formatter import (
    ResponseFormatter,
)

from heshly_core.services.prompt.response_validator import (
    ResponseValidator,
)


class PromptResponseEngine:
    """
    Coordinates prompt composition, AI response generation,
    validation, and formatting.
    """

    def __init__(
        self,
        composer: PromptComposer | None = None,
        generator: ResponseGenerator | None = None,
        validator: ResponseValidator | None = None,
        formatter: ResponseFormatter | None = None,
    ):
        self.composer = composer or PromptComposer()
        self.generator = generator or ResponseGenerator()
        self.validator = validator or ResponseValidator()
        self.formatter = formatter or ResponseFormatter()

    def respond(
        self,
        request: PromptRequest,
        channel: ResponseChannel = ResponseChannel.WHATSAPP,
    ) -> PromptResponse:

        prompt = self.composer.compose(
            request
        )

        response = self.generator.generate(
            prompt
        )

        validation = self.validator.validate(
            response
        )

        if not validation.valid:

            response.message = (
                "I'm sorry, but I couldn't generate a valid response."
            )

            response.confidence = 0.0

        response.message = self.formatter.format(
            response,
            channel,
        )

        return response