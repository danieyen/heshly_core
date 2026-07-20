from heshly_core.models.guardrail import GuardrailAction

from heshly_core.models.handover import (
    HandoverPriority,
    HandoverReason,
)


class HandoverRulesEngine:
    """
    Determines whether a conversation should be handed over
    to a human and assigns an initial priority and reason.
    """

    def evaluate(
        self,
        *,
        guardrail_action: GuardrailAction | None = None,
        urgency: str | None = None,
        customer_requested_human: bool = False,
        ai_confidence: float = 1.0,
    ) -> tuple[bool, HandoverPriority, HandoverReason]:

        # Customer explicitly asked for a human
        if customer_requested_human:
            return (
                True,
                HandoverPriority.HIGH,
                HandoverReason.CUSTOMER_REQUEST,
            )

        # Emergency cases
        if urgency and urgency.lower() == "emergency":
            return (
                True,
                HandoverPriority.EMERGENCY,
                HandoverReason.EMERGENCY,
            )

        # Guardrail escalation
        if guardrail_action == GuardrailAction.ESCALATE:
            return (
                True,
                HandoverPriority.HIGH,
                HandoverReason.GUARDRAIL,
            )

        # Low AI confidence
        if ai_confidence < 0.50:
            return (
                True,
                HandoverPriority.NORMAL,
                HandoverReason.LOW_CONFIDENCE,
            )

        # No handover required
        return (
            False,
            HandoverPriority.NORMAL,
            HandoverReason.OTHER,
        )