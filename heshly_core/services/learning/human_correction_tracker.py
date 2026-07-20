from heshly_core.models.learning import (
    HumanCorrectionRecord,
)


class HumanCorrectionTracker:
    """
    Tracks human corrections to AI decisions.
    """

    def record(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        engine: str,
        original_decision: str,
        corrected_decision: str,
        reason: str,
        corrected_by: str,
    ) -> HumanCorrectionRecord:

        return HumanCorrectionRecord(
            conversation_id=conversation_id,
            customer_id=customer_id,
            engine=engine,
            original_decision=original_decision,
            corrected_decision=corrected_decision,
            reason=reason,
            corrected_by=corrected_by,
        )

    def was_changed(
        self,
        record: HumanCorrectionRecord,
    ) -> bool:

        return (
            record.original_decision
            != record.corrected_decision
        )