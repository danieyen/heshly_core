from __future__ import annotations

from datetime import datetime

import frappe

from heshly_core.models.crm import (
    ActivityType,
    CRMActivity,
)
from heshly_core.repositories.base_repository import BaseRepository


class ActivityRepository(BaseRepository[CRMActivity]):
    """Persistent, tenant-aware CRM activity repository using Communication."""

    DOCTYPE = "Communication"

    ID_FIELD = "custom_heshly_activity_id"
    TENANT_FIELD = "custom_heshly_tenant_id"
    RELATED_TYPE_FIELD = "custom_heshly_related_type"
    RELATED_ID_FIELD = "custom_heshly_related_id"
    ACTIVITY_TYPE_FIELD = "custom_heshly_activity_type"
    PERFORMED_BY_FIELD = "custom_heshly_performed_by"
    PERFORMED_AT_FIELD = "custom_heshly_performed_at"

    def _tenant_id(self) -> str:
        return self.current_tenant()

    def _validate_tenant(self, entity: CRMActivity) -> str:
        tenant_id = self._tenant_id()

        existing_tenant = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.activity_id,
            },
            self.TENANT_FIELD,
        )

        if existing_tenant and existing_tenant != tenant_id:
            raise PermissionError(
                "Activity belongs to another tenant."
            )

        return tenant_id

    def _activity_type_to_frappe(
        self,
        activity_type: ActivityType,
    ) -> str:
        return activity_type.value

    def _activity_type_from_frappe(
        self,
        value: str,
    ) -> ActivityType:
        return ActivityType(value)

    def _to_model(self, doc) -> CRMActivity:
        performed_at = (
            doc.get(self.PERFORMED_AT_FIELD)
            or doc.get("communication_date")
            or doc.creation
        )

        return CRMActivity(
            activity_id=doc.get(self.ID_FIELD),
            related_type=doc.get(self.RELATED_TYPE_FIELD) or "",
            related_id=doc.get(self.RELATED_ID_FIELD) or "",
            activity_type=self._activity_type_from_frappe(
                doc.get(self.ACTIVITY_TYPE_FIELD)
            ),
            description=doc.get("content") or "",
            performed_by=doc.get(self.PERFORMED_BY_FIELD),
            performed_at=performed_at,
        )

    # =====================================================
    # CRUD
    # =====================================================

    def save(self, entity: CRMActivity) -> CRMActivity:
        tenant_id = self._validate_tenant(entity)

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.activity_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if name:
            doc = frappe.get_doc(self.DOCTYPE, name)
        else:
            doc = frappe.new_doc(self.DOCTYPE)

            doc.communication_type = "Communication"
            doc.communication_medium = "Other"
            doc.status = "Open"
            doc.sent_or_received = "Received"

        doc.subject = entity.description[:140] or "CRM Activity"
        doc.content = entity.description

        doc.communication_date = entity.performed_at

        doc.set(
            self.ID_FIELD,
            entity.activity_id,
        )

        doc.set(
            self.TENANT_FIELD,
            tenant_id,
        )

        doc.set(
            self.RELATED_TYPE_FIELD,
            entity.related_type,
        )

        doc.set(
            self.RELATED_ID_FIELD,
            entity.related_id,
        )

        doc.set(
            self.ACTIVITY_TYPE_FIELD,
            self._activity_type_to_frappe(
                entity.activity_type
            ),
        )

        doc.set(
            self.PERFORMED_BY_FIELD,
            entity.performed_by,
        )

        doc.set(
            self.PERFORMED_AT_FIELD,
            entity.performed_at,
        )

        if entity.related_type and entity.related_id:
            if frappe.db.exists(
                entity.related_type,
                entity.related_id,
            ):
                doc.reference_doctype = entity.related_type
                doc.reference_name = entity.related_id

        doc.save(ignore_permissions=True)

        frappe.db.commit()

        return self._to_model(doc)

    def get(
        self,
        entity_id: str,
    ) -> CRMActivity | None:

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
            frappe.get_doc(
                self.DOCTYPE,
                name,
            )
        )

    def list(self) -> list[CRMActivity]:

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
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
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

        return frappe.db.count(
            self.DOCTYPE,
            {
                self.TENANT_FIELD: self._tenant_id(),
            },
        )

    def clear(self) -> None:

        names = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: self._tenant_id(),
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
    ) -> list[CRMActivity]:

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: self._tenant_id(),
                self.RELATED_TYPE_FIELD: related_type,
                self.RELATED_ID_FIELD: related_id,
            },
            fields=["name"],
            order_by=f"{self.PERFORMED_AT_FIELD} desc",
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

    def find_by_type(
        self,
        activity_type: ActivityType,
    ) -> list[CRMActivity]:

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: self._tenant_id(),
                self.ACTIVITY_TYPE_FIELD: activity_type.value,
            },
            fields=["name"],
            order_by=f"{self.PERFORMED_AT_FIELD} desc",
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

    def find_by_user(
        self,
        performed_by: str,
    ) -> list[CRMActivity]:

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: self._tenant_id(),
                self.PERFORMED_BY_FIELD: performed_by,
            },
            fields=["name"],
            order_by=f"{self.PERFORMED_AT_FIELD} desc",
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

    def search(
        self,
        query: str,
    ) -> list[CRMActivity]:

        query = query.strip()

        if not query:
            return self.list()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: self._tenant_id(),
            },
            fields=["name"],
            order_by=f"{self.PERFORMED_AT_FIELD} desc",
        )

        results = []

        for row in rows:
            activity = self._to_model(
                frappe.get_doc(
                    self.DOCTYPE,
                    row.name,
                )
            )

            q = query.lower()

            if (
                q in activity.description.lower()
                or (
                    activity.performed_by
                    and q in activity.performed_by.lower()
                )
                or q in activity.related_type.lower()
            ):
                results.append(activity)

        return results

    # =====================================================
    # Analytics
    # =====================================================

    def count_by_type(
        self,
        activity_type: ActivityType,
    ) -> int:

        return len(
            self.find_by_type(activity_type)
        )

    def count_by_related(
        self,
        related_type: str,
        related_id: str,
    ) -> int:

        return len(
            self.find_by_related(
                related_type,
                related_id,
            )
        )

    def latest(
        self,
        limit: int = 10,
    ) -> list[CRMActivity]:

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: self._tenant_id(),
            },
            fields=["name"],
            order_by=f"{self.PERFORMED_AT_FIELD} desc",
            limit_page_length=limit,
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
