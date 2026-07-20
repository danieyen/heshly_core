from heshly_core.models.learning import (
    ConversationOutcome,
    ConversationOutcomeRecord,
)


class ConversationOutcomeTracker:
    """
    Tracks and stores the final outcome
    of customer conversations.
    """

    def track(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        outcome: ConversationOutcome,
    ) -> ConversationOutcomeRecord:

        return ConversationOutcomeRecord(
            conversation_id=conversation_id,
            customer_id=customer_id,
            outcome=outcome,
        )

    def is_success(
        self,
        outcome: ConversationOutcome,
    ) -> bool:

        return outcome in {
            ConversationOutcome.BOOKED,
            ConversationOutcome.QUALIFIED,
            ConversationOutcome.COMPLETED,
        }