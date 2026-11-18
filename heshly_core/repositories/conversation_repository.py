from __future__ import annotations

from datetime import UTC, datetime

import frappe

from heshly_core.models.conversation import (
    Conversation,
    ConversationStatus,
    ConversationTurn,
    ExtractedEntities,
    Speaker,
)
from heshly_core.repositories.base_repository import BaseRepository


def _frappe_datetime(value):
    """Convert aware datetime to naive UTC for Frappe/MariaDB."""
    if value is None:
        return None

    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)

    return value


def _utc_datetime(value):
    """Convert Frappe naive datetime to aware UTC."""
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


class ConversationRepository(BaseRepository[Conversation]):
    """
    Persistent, tenant-aware repository for AI Conversation.

    AI Conversation is the aggregate root.
    AI Conversation Turn stores the conversation history.

    Tenant isolation is enforced through BaseRepository.
    """

    DOCTYPE = "AI Conversation"

    ID_FIELD = "conversation_id"
    TENANT_FIELD = "tenant_id"

    # =====================================================
    # Tenant
    # =====================================================

    def _tenant_id(
        self,
        tenant_id: str | None = None,
    ) -> str:
        return self.require_tenant(tenant_id)

    # =====================================================
    # Save / Upsert
    # =====================================================

    def save(
        self,
        conversation: Conversation,
        tenant_id: str | None = None,
        channel: str = "whatsapp",
        intent: str | None = None,
    ) -> Conversation:

        tenant_id = self._tenant_id(tenant_id)

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: conversation.conversation_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc(
                self.DOCTYPE,
                existing_name,
            )
        else:
            doc = frappe.new_doc(
                self.DOCTYPE
            )

            doc.conversation_id = (
                conversation.conversation_id
            )

            doc.tenant_id = tenant_id
            doc.customer_id = conversation.customer_id
            doc.channel = channel

            doc.started_at = _frappe_datetime(
                conversation.created_at
            )

        # -------------------------------------------------
        # Tenant / aggregate fields
        # -------------------------------------------------

        doc.tenant_id = tenant_id
        doc.customer_id = conversation.customer_id
        doc.channel = channel
        doc.status = conversation.status.value

        # -------------------------------------------------
        # Extracted entities
        # -------------------------------------------------

        doc.service = conversation.entities.service
        doc.appointment_date = conversation.entities.date
        doc.appointment_time = conversation.entities.time
        doc.customer_name = conversation.entities.customer_name

        doc.customer_phone = (
            conversation.entities.phone
            or conversation.customer_id
        )

        doc.customer_email = conversation.entities.email

        if intent is not None:
            doc.intent = intent

        # -------------------------------------------------
        # Conversation metadata
        # -------------------------------------------------

        doc.turn_count = conversation.turn_count()

        if conversation.turns:
            doc.last_message_at = _frappe_datetime(
                conversation.turns[-1].timestamp
            )
        else:
            doc.last_message_at = _frappe_datetime(
                conversation.updated_at
            )

        # -------------------------------------------------
        # Rebuild child table
        # -------------------------------------------------

        doc.set("turns", [])

        for turn in conversation.turns:

            row = doc.append(
                "turns",
                {},
            )

            row.role = turn.role.value
            row.message = turn.message

            row.timestamp = _frappe_datetime(
                turn.timestamp
            )

        # -------------------------------------------------
        # Persist
        # -------------------------------------------------

        doc.flags.ignore_permissions = True

        if doc.is_new():
            doc.insert(
                ignore_permissions=True
            )
        else:
            doc.save(
                ignore_permissions=True
            )

        frappe.db.commit()

        return conversation

    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        conversation_id: str,
        tenant_id: str | None = None,
    ) -> Conversation | None:

        tenant_id = self._tenant_id(tenant_id)

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: conversation_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        doc = frappe.get_doc(
            self.DOCTYPE,
            name,
        )

        entities = ExtractedEntities(
            service=doc.service,
            date=doc.appointment_date,
            time=doc.appointment_time,
            customer_name=doc.customer_name,
            phone=doc.customer_phone,
            email=doc.customer_email,
        )

        turns: list[ConversationTurn] = []

        for row in doc.turns or []:

            timestamp = row.timestamp

            if timestamp is None:
                timestamp = datetime.now(UTC)
            else:
                timestamp = _utc_datetime(
                    timestamp
                )

            turns.append(
                ConversationTurn(
                    role=Speaker(row.role),
                    message=row.message,
                    timestamp=timestamp,
                )
            )

        created_at = (
            _utc_datetime(doc.started_at)
            if doc.started_at
            else datetime.now(UTC)
        )

        updated_at = (
            _utc_datetime(doc.last_message_at)
            if doc.last_message_at
            else created_at
        )

        return Conversation(
            conversation_id=doc.conversation_id,
            customer_id=doc.customer_id,
            status=ConversationStatus(
                doc.status
                or ConversationStatus.ACTIVE.value
            ),
            entities=entities,
            turns=turns,
            created_at=created_at,
            updated_at=updated_at,
        )

    # =====================================================
    # Exists
    # =====================================================

    def exists(
        self,
        conversation_id: str,
        tenant_id: str | None = None,
    ) -> bool:

        tenant_id = self._tenant_id(tenant_id)

        return bool(
            frappe.db.exists(
                self.DOCTYPE,
                {
                    self.ID_FIELD: conversation_id,
                    self.TENANT_FIELD: tenant_id,
                },
            )
        )

    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        conversation_id: str,
        tenant_id: str | None = None,
    ) -> None:

        tenant_id = self._tenant_id(tenant_id)

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: conversation_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return

        frappe.delete_doc(
            self.DOCTYPE,
            name,
            ignore_permissions=True,
        )

        frappe.db.commit()

    # =====================================================
    # All
    # =====================================================

    def all(
        self,
        tenant_id: str | None = None,
    ) -> list[Conversation]:

        tenant_id = self._tenant_id(tenant_id)

        names = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            pluck=self.ID_FIELD,
            order_by="modified desc",
        )

        conversations: list[Conversation] = []

        for name in names:

            conversation = self.get(
                name,
                tenant_id=tenant_id,
            )

            if conversation is not None:
                conversations.append(
                    conversation
                )

        return conversations

    # =====================================================
    # Count
    # =====================================================

    def count(
        self,
        tenant_id: str | None = None,
    ) -> int:

        tenant_id = self._tenant_id(tenant_id)

        return frappe.db.count(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
        )

    # =====================================================
    # Queries
    # =====================================================

    def find_by_customer(
        self,
        customer_id: str,
        tenant_id: str | None = None,
    ) -> list[Conversation]:

        tenant_id = self._tenant_id(tenant_id)

        names = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                "customer_id": customer_id,
            },
            pluck=self.ID_FIELD,
            order_by="modified desc",
        )

        return [
            conversation
            for name in names
            if (
                conversation := self.get(
                    name,
                    tenant_id=tenant_id,
                )
            ) is not None
        ]

    def find_by_status(
        self,
        status: ConversationStatus | str,
        tenant_id: str | None = None,
    ) -> list[Conversation]:

        tenant_id = self._tenant_id(tenant_id)

        if isinstance(status, ConversationStatus):
            status = status.value

        names = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                "status": status,
            },
            pluck=self.ID_FIELD,
            order_by="modified desc",
        )

        return [
            conversation
            for name in names
            if (
                conversation := self.get(
                    name,
                    tenant_id=tenant_id,
                )
            ) is not None
        ]
