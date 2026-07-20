from heshly_core.models.handover import (
    HandoverPriority,
    HumanQueue,
)


class HumanQueueManager:
    """
    Routes handovers to the appropriate human queue.
    """

    def select_queue(
        self,
        *,
        priority: HandoverPriority,
        department: str,
    ) -> HumanQueue:

        if priority == HandoverPriority.EMERGENCY:

            return HumanQueue(
                name="Emergency Queue",
                priority=priority,
                department=department,
                available_agents=1,
            )

        if priority == HandoverPriority.HIGH:

            return HumanQueue(
                name="Priority Queue",
                priority=priority,
                department=department,
                available_agents=2,
            )

        return HumanQueue(
            name="General Queue",
            priority=priority,
            department=department,
            available_agents=5,
        )