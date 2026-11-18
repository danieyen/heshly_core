from __future__ import annotations

from heshly_core.models.conversation import Conversation
from heshly_core.repositories.conversation_repository import (
    ConversationRepository,
)
from heshly_core.services.tenant.tenant_context import TenantContext


class ConversationStore:
    """
    Persistent conversation store.

    Kept as the ConversationManager-facing abstraction while
    persistence is delegated to the Frappe repository.
    """

    def __init__(
        self,
        tenant_id: str | None = None,
        channel: str = "whatsapp",
    ):
        self.tenant_id = (
            tenant_id
            if tenant_id is not None
            else TenantContext().require()
        )
        self.channel = channel
        self.repository = ConversationRepository()

    def save(
        self,
        conversation: Conversation,
    ) -> None:

        self.repository.save(
            conversation,
            tenant_id=self.tenant_id,
            channel=self.channel,
        )

    def get(
        self,
        conversation_id: str,
    ) -> Conversation | None:

        return self.repository.get(
            conversation_id,
            tenant_id=self.tenant_id,
        )

    def exists(
        self,
        conversation_id: str,
    ) -> bool:

        return self.repository.exists(
            conversation_id,
            tenant_id=self.tenant_id,
        )

    def delete(
        self,
        conversation_id: str,
    ) -> None:

        self.repository.delete(
            conversation_id,
            tenant_id=self.tenant_id,
        )

    def all(self) -> list[Conversation]:

        return self.repository.all(
            tenant_id=self.tenant_id,
        )

    def count(self) -> int:

        return self.repository.count(
            tenant_id=self.tenant_id,
        )
