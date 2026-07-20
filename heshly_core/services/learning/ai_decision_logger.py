from heshly_core.models.learning import (
    AIDecisionRecord,
)


class AIDecisionLogger:
    """
    Records AI decisions for auditing,
    analytics and future learning.
    """

    def log(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        engine: str,
        decision: str,
        confidence: float,
        reasoning: str,
        metadata: dict[str, str] | None = None,
    ) -> AIDecisionRecord:

        return AIDecisionRecord(
            conversation_id=conversation_id,
            customer_id=customer_id,
            engine=engine,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {},
        )

    def high_confidence(
        self,
        record: AIDecisionRecord,
    ) -> bool:

        return record.confidence >= 0.80