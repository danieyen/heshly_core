from heshly_core.models.guardrail import GuardrailAction

from heshly_core.models.handover import (
    EscalationTriggers,
)


class EscalationTriggerEvaluator:
    """
    Collects escalation signals from multiple AI engines.
    """

    def evaluate(
        self,
        *,
        guardrail_action: GuardrailAction = GuardrailAction.ALLOW,
        customer_requested_human: bool = False,
        urgency: str = "low",
        ai_confidence: float = 1.0,
        qualification_passed: bool = True,
        booking_successful: bool = True,
        conversation_stalled: bool = False,
    ) -> EscalationTriggers:

        return EscalationTriggers(

            customer_requested_human=customer_requested_human,

            guardrail_escalation=(
                guardrail_action == GuardrailAction.ESCALATE
            ),

            emergency=(
                urgency.lower() == "emergency"
            ),

            low_ai_confidence=(
                ai_confidence < 0.50
            ),

            qualification_failed=(
                not qualification_passed
            ),

            booking_failed=(
                not booking_successful
            ),

            conversation_stalled=conversation_stalled,
        )