from __future__ import annotations

from datetime import UTC, datetime

import frappe

from heshly_core.models.crm import WhatsAppActivity
from heshly_core.repositories.base_repository import BaseRepository


def _utc_datetime(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


class WhatsAppActivityRepository(BaseRepository[WhatsAppActivity]):
    """Persistent, tenant-aware WhatsApp activity repository."""

    DOCTYPE = "Heshly WhatsApp Activity"

    def __init__(
        self,
        tenant_id: str | None = None,
    ) -> None:
        super().__init__()
        self._explicit_tenant_id = tenant_id

    def set_tenant(self, tenant_id: str) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required.")

        self._explicit_tenant_id = tenant_id

    def _tenant_id(self) -> str:
        if self._explicit_tenant_id:
            return self._explicit_tenant_id

        return self.current_tenant()

    ID_FIELD = "activity_id"
    TENANT_FIELD = "tenant_id"
    BUSINESS_FIELD = "business_id"
    RELATED_TYPE_FIELD = "related_type"
    RELATED_ID_FIELD = "related_id"
    MESSAGE_ID_FIELD = "message_id"
    DIRECTION_FIELD = "direction"
    PHONE_FIELD = "phone_number"
    MESSAGE_FIELD = "message"
    STATUS_FIELD = "status"
    LOGGED_BY_FIELD = "logged_by"

    def _validate_tenant(self, entity: WhatsAppActivity) -> str:
        tenant_id = self._tenant_id()

        existing_tenant = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.activity_id,
            },
            self.TENANT_FIELD,
        )

        if existing_tenant and existing_tenant != tenant_id:
            raise ValueError(
                "Cross-tenant WhatsApp activity access denied."
            )

        return tenant_id

    def _to_model(self, doc) -> WhatsAppActivity:
        return WhatsAppActivity(
            activity_id=doc.get(self.ID_FIELD),
            business_id=doc.get(self.BUSINESS_FIELD),
            related_type=doc.get(self.RELATED_TYPE_FIELD),
            related_id=doc.get(self.RELATED_ID_FIELD),
            message_id=doc.get(self.MESSAGE_ID_FIELD),
            direction=doc.get(self.DIRECTION_FIELD),
            phone_number=doc.get(self.PHONE_FIELD),
            message=doc.get(self.MESSAGE_FIELD),
            status=doc.get(self.STATUS_FIELD),
            logged_by=doc.get(self.LOGGED_BY_FIELD),
            tenant_id=doc.get(self.TENANT_FIELD),
            created_at=(
                _utc_datetime(doc.get("created_at"))
                if doc.get("created_at")
                else datetime.now(UTC)
            ),
        )

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: WhatsAppActivity,
    ) -> WhatsAppActivity:

        tenant_id = self._validate_tenant(entity)

        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.activity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc(self.DOCTYPE, existing_name)
        else:
            doc = frappe.new_doc(self.DOCTYPE)

        doc.activity_id = entity.activity_id
        doc.tenant_id = tenant_id
        doc.business_id = entity.business_id
        doc.related_type = entity.related_type
        doc.related_id = entity.related_id
        doc.message_id = entity.message_id
        doc.direction = entity.direction
        doc.phone_number = entity.phone_number
        doc.message = entity.message
        doc.status = entity.status
        doc.logged_by = entity.logged_by
        doc.created_at = entity.created_at

        doc.flags.ignore_permissions = True

        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)

        frappe.db.commit()

        return self._to_model(doc)

    def get(
        self,
        entity_id: str,
    ) -> WhatsAppActivity | None:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(self.DOCTYPE, name)
        )

    def list(self) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation asc",
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if not name:
            return False

        frappe.delete_doc(
            self.DOCTYPE,
            name,
            ignore_permissions=True,
        )

        frappe.db.commit()

        return True

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return self.get(entity_id) is not None

    def count(self) -> int:

        tenant_id = self._tenant_id()

        return frappe.db.count(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
        )

    def clear(self) -> None:

        tenant_id = self._tenant_id()

        names = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            pluck="name",
        )

        for name in names:
            frappe.delete_doc(
                self.DOCTYPE,
                name,
                ignore_permissions=True,
            )

        frappe.db.commit()

    # =====================================================
    # Queries
    # =====================================================

    def find_by_related(
        self,
        related_type: str,
        related_id: str,
    ) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                self.RELATED_TYPE_FIELD: related_type,
                self.RELATED_ID_FIELD: related_id,
            },
            fields=["name"],
            order_by="creation asc",
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]

    def find_by_phone(
        self,
        phone_number: str,
    ) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                self.PHONE_FIELD: phone_number,
            },
            fields=["name"],
            order_by="creation asc",
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]

    def find_by_message_id(
        self,
        message_id: str,
    ) -> WhatsAppActivity | None:

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.TENANT_FIELD: tenant_id,
                self.MESSAGE_ID_FIELD: message_id,
            },
            "name",
        )

        if not name:
            return None

        return self._to_model(
            frappe.get_doc(self.DOCTYPE, name)
        )

    def update_status_by_message_id(
        self,
        message_id: str,
        status: str,
    ) -> WhatsAppActivity | None:
        """Update a WhatsApp activity status by Meta message ID."""

        if not message_id:
            raise ValueError("message_id is required.")

        if not status:
            raise ValueError("status is required.")

        tenant_id = self._tenant_id()

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.TENANT_FIELD: tenant_id,
                self.MESSAGE_ID_FIELD: message_id,
            },
            "name",
        )

        if not name:
            return None

        doc = frappe.get_doc(
            self.DOCTYPE,
            name,
        )

        # Meta webhooks can arrive more than once and may arrive
        # out of order. Never allow an older lifecycle state to
        # overwrite a newer one.
        status_rank = {
            "pending": 0,
            "sent": 1,
            "delivered": 2,
            "read": 3,
            "failed": 3,
            "received": 3,
        }

        current_status = str(
            doc.status or ""
        ).strip().lower()

        incoming_status = str(
            status
        ).strip().lower()

        current_rank = status_rank.get(
            current_status,
            -1,
        )

        incoming_rank = status_rank.get(
            incoming_status,
            -1,
        )

        if (
            current_rank >= 0
            and incoming_rank >= 0
            and incoming_rank < current_rank
        ):
            return self._to_model(doc)

        doc.status = incoming_status
        doc.flags.ignore_permissions = True

        doc.save(
            ignore_permissions=True
        )

        frappe.db.commit()

        return self._to_model(doc)

    def find_by_direction(
        self,
        direction: str,
    ) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                self.DIRECTION_FIELD: direction,
            },
            fields=["name"],
            order_by="creation asc",
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]

    def find_by_status(
        self,
        status: str,
    ) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                self.STATUS_FIELD: status,
            },
            fields=["name"],
            order_by="creation asc",
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]

    def search(
        self,
        query: str,
    ) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()
        query = query.strip()

        if not query:
            return []

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            or_filters=[
                [self.MESSAGE_FIELD, "like", f"%{query}%"],
                [self.PHONE_FIELD, "like", f"%{query}%"],
                [self.RELATED_ID_FIELD, "like", f"%{query}%"],
                [self.MESSAGE_ID_FIELD, "like", f"%{query}%"],
            ],
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]

    # =====================================================
    # Analytics
    # =====================================================

    def count_by_status(
        self,
        status: str,
    ) -> int:

        return len(self.find_by_status(status))

    def count_by_direction(
        self,
        direction: str,
    ) -> int:

        return len(self.find_by_direction(direction))

    def latest(
        self,
        limit: int = 10,
    ) -> list[WhatsAppActivity]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
            limit_page_length=limit,
        )

        return [
            self._to_model(
                frappe.get_doc(self.DOCTYPE, row.name)
            )
            for row in rows
        ]
