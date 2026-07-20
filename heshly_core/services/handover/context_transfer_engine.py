from heshly_core.models.handover import (
    ContextTransfer,
    ConversationSummary,
)


class ContextTransferEngine:
    """
    Packages all information required by a human
    agent to continue the conversation.
    """

    def build(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        summary: ConversationSummary,
        messages: list[str] | None = None,
        customer_memory: dict[str, str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ContextTransfer:

        return ContextTransfer(
            conversation_id=conversation_id,
            customer_id=customer_id,
            summary=summary,
            messages=messages or [],
            customer_memory=customer_memory or {},
            metadata=metadata or {},
        )