from heshly_core.models.handover import (
    ContextTransfer,
    HandoverNotification,
    HumanQueue,
)


class HandoverNotificationManager:
    """
    Creates notifications for human agents or queues.
    """

    def create(
        self,
        *,
        queue: HumanQueue,
        context: ContextTransfer,
    ) -> HandoverNotification:

        customer = (
            context.summary.customer_name
            or context.customer_id
        )

        service = (
            context.summary.requested_service
            or "Unknown service"
        )

        return HandoverNotification(
            recipient=queue.name,
            title="New Human Handover",
            message=(
                f"{customer} requires assistance "
                f"for {service}."
            ),
            priority=queue.priority,
        )