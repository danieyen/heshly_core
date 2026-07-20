from heshly_core.models.handover import (
    ContextTransfer,
    HandoverRequest,
    HandoverStatus,
    HumanTakeover,
)


class HumanTakeoverManager:
    """
    Transfers ownership of a conversation
    from the AI to a human agent.
    """

    def begin(
        self,
        *,
        request: HandoverRequest,
        context: ContextTransfer,
        agent_id: str,
    ) -> HumanTakeover:

        request.assigned_to = agent_id

        request.status = HandoverStatus.IN_PROGRESS

        context.metadata["owner"] = "human"

        context.metadata["agent_id"] = agent_id

        return HumanTakeover(
            conversation_id=request.conversation_id,
            customer_id=request.customer_id,
            agent_id=agent_id,
            ai_active=False,
        )