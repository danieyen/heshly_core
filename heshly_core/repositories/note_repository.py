from __future__ import annotations

from datetime import datetime

import frappe

from heshly_core.models.crm import CRMNote
from heshly_core.repositories.base_repository import BaseRepository


class NoteRepository(BaseRepository[CRMNote]):
    """Persistent, tenant-aware CRM note repository using Frappe Note."""

    DOCTYPE = "Note"

    TENANT_FIELD = "custom_heshly_tenant_id"
    ID_FIELD = "custom_heshly_note_id"
    RELATED_TYPE_FIELD = "custom_heshly_related_type"
    RELATED_ID_FIELD = "custom_heshly_related_id"
    ADDED_BY_FIELD = "custom_heshly_added_by"
    ADDED_ON_FIELD = "custom_heshly_added_on"

    def _tenant_id(self) -> str:
        return self.current_tenant()

    def _validate_tenant(self, note: CRMNote) -> str:
        tenant_id = self._tenant_id()

        existing_tenant = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: note.note_id,
            },
            self.TENANT_FIELD,
        )

        if existing_tenant and existing_tenant != tenant_id:
            raise PermissionError(
                "Note belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Mapping
    # =====================================================

    def _to_model(self, doc) -> CRMNote:
        return CRMNote(
            note_id=doc.custom_heshly_note_id,
            related_type=doc.custom_heshly_related_type or "",
            related_id=doc.custom_heshly_related_id or "",
            content=doc.content or "",
            created_by=(
                doc.custom_heshly_added_by
                or doc.owner
                or ""
            ),
            created_at=(
                doc.custom_heshly_added_on
                or doc.creation
            ),
        )

    # =====================================================
    # Save
    # =====================================================

    def save(self, entity: CRMNote) -> CRMNote:
        tenant_id = self._validate_tenant(entity)

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.note_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if name:
            doc = frappe.get_doc(self.DOCTYPE, name)
        else:
            doc = frappe.new_doc(self.DOCTYPE)

        doc.title = (
            entity.content[:80]
            if entity.content
            else entity.note_id
        )

        doc.content = entity.content

        doc.custom_heshly_note_id = entity.note_id
        doc.custom_heshly_tenant_id = tenant_id
        doc.custom_heshly_related_type = entity.related_type
        doc.custom_heshly_related_id = entity.related_id
        doc.custom_heshly_added_by = (
            entity.created_by or frappe.session.user
        )
        doc.custom_heshly_added_on = (
            entity.created_at or datetime.utcnow()
        )

        doc.flags.ignore_permissions = True

        doc.save(
            ignore_permissions=True,
        )

        frappe.db.commit()

        return self._to_model(doc)

    # =====================================================
    # Get
    # =====================================================

    def get(self, entity_id: str) -> CRMNote | None:
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

    # =====================================================
    # List
    # =====================================================

    def list(self) -> list[CRMNote]:
        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    # =====================================================
    # Delete
    # =====================================================

    def delete(self, entity_id: str) -> bool:
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

    def exists(self, entity_id: str) -> bool:
        return self.get(entity_id) is not None

    def count(self) -> int:
        return frappe.db.count(
            self.DOCTYPE,
            {
                self.TENANT_FIELD: self._tenant_id(),
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
    ) -> list[CRMNote]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                self.RELATED_TYPE_FIELD: related_type,
                self.RELATED_ID_FIELD: related_id,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]

    def find_by_author(
        self,
        created_by: str,
    ) -> list[CRMNote]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                self.ADDED_BY_FIELD: created_by,
            },
            fields=["name"],
            order_by="creation desc",
        )

        return [
            self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )
            for row in rows
        ]
