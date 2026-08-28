from datetime import datetime, UTC
from typing import Any

from heshly_core.models.conversation import (
    Conversation,
    ConversationStatus,
    ConversationTurn,
    Speaker,
)

from heshly_core.services.conversation.conversation_store import (
    ConversationStore,
)


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]")):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


class ConversationManager:
    """
    Central coordinator for conversation lifecycle.

    Responsibilities:
    - Create conversations
    - Manage conversation turns
    - Manage status changes
    - Coordinate cache
    - Coordinate persistence
    - Recover interrupted conversations
    """


    def __init__(
        self,
        store: ConversationStore | None = None,
        cache=None,
        lifecycle=None,
        recovery=None,
        tenant_id: str | None = None,
        channel: str = "whatsapp",
    ):
        # Tenant must be explicit or resolved via TenantContext inside store.
        # Do not default to "default" - that breaks tenant isolation.
        if tenant_id is not None:
            self.store = store or ConversationStore(
                tenant_id=tenant_id,
                channel=channel,
            )
        else:
            self.store = store or ConversationStore(
                channel=channel,
            )

        self.cache = cache
        self.lifecycle = lifecycle
        self.recovery = recovery


    # ---------------------------------------------------------
    # Conversation Creation
    # ---------------------------------------------------------

    def create(
        self,
        conversation_id: str,
        customer_id: str,
    ) -> Conversation:

        if not conversation_id:
            raise ValueError("conversation_id is required")
        if not customer_id:
            raise ValueError("customer_id is required")

        conversation = Conversation(
            conversation_id=conversation_id,
            customer_id=customer_id,
        )

        if self.lifecycle:
            self.lifecycle.start(conversation)

        self.save(conversation)

        return conversation

    def create_from_dict(self, data: Any) -> Conversation:
        """
        Create from n8n payload that may be JSON string or nested under body.
        """
        data = _parse_json_if_string(data)
        if isinstance(data, dict) and "body" in data and isinstance(data["body"], dict):
            # Handle n8n $json.body nesting
            data = data["body"]
        if isinstance(data, dict) and "json" in data and isinstance(data["json"], dict):
            data = data["json"]
        conversation = Conversation.from_dict(data)
        if self.lifecycle:
            self.lifecycle.start(conversation)
        self.save(conversation)
        return conversation


    # ---------------------------------------------------------
    # Message Handling
    # ---------------------------------------------------------

    def add_user_message(
        self,
        conversation: Conversation,
        message: str,
    ) -> None:

        if not message:
            raise ValueError("message is required")

        conversation.add_turn(
            ConversationTurn(
                role=Speaker.USER,
                message=message,
            )
        )

        conversation.updated_at = datetime.now(UTC)


    def add_assistant_message(
        self,
        conversation: Conversation,
        message: str,
    ) -> None:

        if not message:
            raise ValueError("message is required")

        conversation.add_turn(
            ConversationTurn(
                role=Speaker.ASSISTANT,
                message=message,
            )
        )

        conversation.updated_at = datetime.now(UTC)


    def add_system_message(
        self,
        conversation: Conversation,
        message: str,
    ) -> None:

        if not message:
            raise ValueError("message is required")

        conversation.add_turn(
            ConversationTurn(
                role=Speaker.SYSTEM,
                message=message,
            )
        )

        conversation.updated_at = datetime.now(UTC)



    # ---------------------------------------------------------
    # Lifecycle Management
    # ---------------------------------------------------------

    def set_status(
        self,
        conversation: Conversation,
        status: Any,
    ) -> None:

        # Handle string status from n8n Switch nodes
        if isinstance(status, str):
            status = ConversationStatus.from_value(status)
        if not isinstance(status, ConversationStatus):
            raise ValueError(f"status must be ConversationStatus, got {status}")
        conversation.status = status
        conversation.updated_at = datetime.now(UTC)



    def close(
        self,
        conversation: Conversation,
    ) -> None:

        if self.lifecycle:
            self.lifecycle.complete(conversation)

        else:
            self.set_status(
                conversation,
                ConversationStatus.COMPLETED,
            )

        self.save(conversation)



    def handover(
        self,
        conversation: Conversation,
    ) -> None:

        if self.lifecycle:
            self.lifecycle.escalate(conversation)

        else:
            self.set_status(
                conversation,
                ConversationStatus.HANDOVER,
            )

        self.save(conversation)



    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get(
        self,
        conversation_id: str,
    ) -> Conversation | None:

        if not conversation_id:
            raise ValueError("conversation_id is required")

        # Handle n8n passing JSON string or nested object
        if isinstance(conversation_id, dict):
            # Extract from n8n $json.body
            conversation_id = conversation_id.get("conversation_id") or conversation_id.get("conversationId") or conversation_id.get("id") or ""
            if isinstance(conversation_id, dict):
                conversation_id = str(conversation_id)
        conversation_id = str(conversation_id).strip()
        if not conversation_id:
            raise ValueError("conversation_id is required")

        # 1. Check cache

        if self.cache:

            cached = self.cache.get(
                conversation_id
            )

            if cached:
                return cached



        # 2. Check store

        conversation = self.store.get(
            conversation_id
        )


        # 3. Restore cache

        if conversation and self.cache:

            self.cache.put(
                conversation
            )


        return conversation



    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    def save(
        self,
        conversation: Conversation,
    ) -> None:

        if isinstance(conversation, dict) or isinstance(conversation, str):
            conversation = Conversation.from_dict(_parse_json_if_string(conversation))

        conversation.updated_at = datetime.now(UTC)

        self.store.save(
            conversation
        )


        if self.cache:

            self.cache.put(
                conversation
            )



    def delete(
        self,
        conversation_id: str,
    ) -> None:

        if not conversation_id:
            raise ValueError("conversation_id is required")

        if self.cache:

            self.cache.remove(
                conversation_id
            )


        self.store.delete(
            conversation_id
        )



    # ---------------------------------------------------------
    # Recovery
    # ---------------------------------------------------------

    def recover(
        self,
        conversation_id: str,
    ) -> Conversation | None:

        if not conversation_id:
            raise ValueError("conversation_id is required")

        if not self.recovery:
            return self.get(conversation_id)


        conversation = self.get(
            conversation_id
        )


        if not conversation:
            return None



        if self.recovery.needs_recovery(
            conversation
        ):

            self.recovery.recover(
                conversation
            )

            self.save(
                conversation
            )


        return conversation
