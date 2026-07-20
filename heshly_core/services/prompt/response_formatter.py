from heshly_core.models.prompt import (
    PromptResponse,
    ResponseChannel,
)


class ResponseFormatter:
    """
    Formats AI responses for different delivery channels.
    """

    def format(
        self,
        response: PromptResponse,
        channel: ResponseChannel = ResponseChannel.WHATSAPP,
    ) -> str:

        message = response.message.strip()

        if channel == ResponseChannel.WHATSAPP:

            return message

        if channel == ResponseChannel.SMS:

            return message[:160]

        if channel == ResponseChannel.WEB:

            return message

        if channel == ResponseChannel.EMAIL:

            return message

        if channel == ResponseChannel.VOICE:

            return (
                message
                .replace("😊", "")
                .replace("👍", "")
                .replace("👋", "")
            )

        return message