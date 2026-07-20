from heshly_core.models.prompt import (
    PromptContext,
    PromptRequest,
)


class PromptComposer:
    """
    Combines all prompt sections into the final prompt.
    """

    def compose(
        self,
        request: PromptRequest,
    ) -> str:

        context = request.context

        sections = []

        if context.system_prompt:
            sections.append(
                context.system_prompt.strip()
            )

        if context.business_context:
            sections.append(
                context.business_context.strip()
            )

        if context.memory_context:
            sections.append(
                context.memory_context.strip()
            )

        if context.conversation_context:
            sections.append(
                context.conversation_context.strip()
            )

        sections.append(
            "Current Customer Message:"
        )

        sections.append(
            request.customer_message.strip()
        )

        return "\n\n".join(sections)