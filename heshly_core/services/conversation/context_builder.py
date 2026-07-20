from heshly_core.models.conversation import Conversation


class ContextBuilder:
    """
    Builds a structured context dictionary for downstream AI components.
    """

    def __init__(self, conversation: Conversation):
        self.conversation = conversation

    def build(self) -> dict:
        return {
            "conversation_id": self.conversation.conversation_id,
            "customer_id": self.conversation.customer_id,
            "status": self.conversation.status.value,
            "turn_count": self.conversation.turn_count(),
            "last_message": self.conversation.last_message(),
            "entities": {
                "service": self.conversation.entities.service,
                "date": self.conversation.entities.date,
                "time": self.conversation.entities.time,
                "customer_name": self.conversation.entities.customer_name,
                "phone": self.conversation.entities.phone,
                "email": self.conversation.entities.email,
                "extras": self.conversation.entities.extras,
            },
            "history": [
                {
                    "role": turn.role.value,
                    "message": turn.message,
                    "timestamp": turn.timestamp.isoformat(),
                }
                for turn in self.conversation.turns
            ],
        }