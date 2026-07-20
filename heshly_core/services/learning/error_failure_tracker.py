from heshly_core.models.learning import (
    FailureRecord,
    FailureType,
)


class ErrorFailureTracker:
    """
    Records operational failures
    for monitoring and future analysis.
    """

    def track(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        failure_type: FailureType,
        source: str,
        message: str,
        recoverable: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> FailureRecord:

        return FailureRecord(
            conversation_id=conversation_id,
            customer_id=customer_id,
            failure_type=failure_type,
            source=source,
            message=message,
            recoverable=recoverable,
            metadata=metadata or {},
        )

    def requires_attention(
        self,
        failure: FailureRecord,
    ) -> bool:

        return not failure.recoverable