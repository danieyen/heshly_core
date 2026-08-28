from datetime import datetime, UTC

from heshly_core.models.conversation import (
    Conversation,
    ConversationStatus,
    ConversationTurn,
    Speaker,
)

from heshly_core.services.conversation.conversation_store import (
    ConversationStore,
)


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
        tenant_id: str = "default",
        channel: str = "whatsapp",
    ):
        self.store = store or ConversationStore(
            tenant_id=tenant_id,
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

        conversation = Conversation(
            conversation_id=conversation_id,
            customer_id=customer_id,
        )

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
        status: ConversationStatus,
    ) -> None:

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
