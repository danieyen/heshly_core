from heshly_core.models.guardrail import GuardrailAction

from heshly_core.services.handover.handover_conversation_flow import (
    HandoverConversationFlow,
)


class HumanHandoverEngine:
    """
    Public entry point for the Human Handover module.

    Coordinates AI-to-human escalation without exposing
    the internal implementation details.
    """

    def __init__(self):

        self.flow = HandoverConversationFlow()

    def process(
        self,
        *,
        customer_id: str,
        conversation_id: str,
        department: str,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        requested_service: str | None = None,
        qualification_status: str | None = None,
        urgency: str = "low",
        booking_recommendation: str | None = None,
        escalation_reason: str | None = None,
        messages: list[str] | None = None,
        customer_memory: dict[str, str] | None = None,
        agent_id: str = "agent001",
        guardrail_action: GuardrailAction = GuardrailAction.ALLOW,
        ai_confidence: float = 1.0,
        customer_requested_human: bool = False,
    ):

        return self.flow.execute(
            customer_id=customer_id,
            conversation_id=conversation_id,
            department=department,
            customer_name=customer_name,
            customer_phone=customer_phone,
            requested_service=requested_service,
            qualification_status=qualification_status,
            urgency=urgency,
            booking_recommendation=booking_recommendation,
            escalation_reason=escalation_reason,
            messages=messages,
            customer_memory=customer_memory,
            agent_id=agent_id,
            guardrail_action=guardrail_action,
            ai_confidence=ai_confidence,
            customer_requested_human=customer_requested_human,
        )