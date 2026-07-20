from heshly_core.models.guardrail import GuardrailAction

from heshly_core.models.handover import (
    ContextTransfer,
    ConversationSummary,
    HandoverRequest,
)

from heshly_core.services.handover.escalation_trigger_evaluator import (
    EscalationTriggerEvaluator,
)

from heshly_core.services.handover.handover_rules_engine import (
    HandoverRulesEngine,
)

from heshly_core.services.handover.human_queue_manager import (
    HumanQueueManager,
)

from heshly_core.services.handover.conversation_summary_builder import (
    ConversationSummaryBuilder,
)

from heshly_core.services.handover.context_transfer_engine import (
    ContextTransferEngine,
)

from heshly_core.services.handover.handover_notification_manager import (
    HandoverNotificationManager,
)

from heshly_core.services.handover.human_takeover_manager import (
    HumanTakeoverManager,
)


class HandoverConversationFlow:
    """
    Coordinates the complete AI-to-human handover workflow.
    """

    def __init__(self):

        self.triggers = EscalationTriggerEvaluator()

        self.rules = HandoverRulesEngine()

        self.summary_builder = ConversationSummaryBuilder()

        self.context_engine = ContextTransferEngine()

        self.queue_manager = HumanQueueManager()

        self.notifications = HandoverNotificationManager()

        self.takeover = HumanTakeoverManager()

    def execute(
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

        trigger = self.triggers.evaluate(
            guardrail_action=guardrail_action,
            customer_requested_human=customer_requested_human,
            urgency=urgency,
            ai_confidence=ai_confidence,
        )

        should_handover, priority, reason = self.rules.evaluate(
            guardrail_action=guardrail_action,
            urgency=urgency,
            customer_requested_human=trigger.customer_requested_human,
            ai_confidence=ai_confidence,
        )

        if not should_handover:
            return None

        summary = self.summary_builder.build(
            customer_name=customer_name,
            customer_phone=customer_phone,
            requested_service=requested_service,
            qualification_status=qualification_status,
            urgency=urgency,
            booking_recommendation=booking_recommendation,
            escalation_reason=(
                escalation_reason
                or reason.value
            ),
        )

        context = self.context_engine.build(
            conversation_id=conversation_id,
            customer_id=customer_id,
            summary=summary,
            messages=messages,
            customer_memory=customer_memory,
        )

        queue = self.queue_manager.select_queue(
            priority=priority,
            department=department,
        )

        request = HandoverRequest(
            customer_id=customer_id,
            conversation_id=conversation_id,
            priority=priority,
            reason=reason,
            queue=queue,
            summary=summary,
        )

        notification = self.notifications.create(
            queue=queue,
            context=context,
        )

        takeover = self.takeover.begin(
            request=request,
            context=context,
            agent_id=agent_id,
        )

        return {
            "request": request,
            "context": context,
            "notification": notification,
            "takeover": takeover,
        }