from __future__ import annotations

from datetime import date

import frappe

from heshly_core.models.crm import (
    CRMTask,
    TaskPriority,
    TaskStatus,
)

from heshly_core.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[CRMTask]):
    """Persistent, tenant-aware CRM task repository using ERPNext ToDo."""

    DOCTYPE = "ToDo"
    TENANT_FIELD = "custom_heshly_tenant_id"
    ID_FIELD = "custom_heshly_task_id"
    TITLE_FIELD = "custom_heshly_title"

    def _tenant_id(self) -> str:
        return self.current_tenant()

    def _validate_tenant(self, task: CRMTask) -> str:
        tenant_id = self._tenant_id()

        existing_tenant = frappe.db.get_value(
            self.DOCTYPE,
            {self.ID_FIELD: task.task_id},
            self.TENANT_FIELD,
        )

        if existing_tenant and existing_tenant != tenant_id:
            raise PermissionError(
                "Task belongs to a different tenant."
            )

        return tenant_id

    # =====================================================
    # Mapping
    # =====================================================

    def _to_model(self, doc) -> CRMTask:
        return CRMTask(
            task_id=doc.custom_heshly_task_id,
            related_type=doc.reference_type or "",
            related_id=doc.reference_name or "",
            title=doc.custom_heshly_title or "",
            description=doc.description or "",
            assigned_to=doc.allocated_to or None,
            due_date=doc.date,
            priority=self._priority_from_frappe(doc.priority),
            status=self._status_from_frappe(doc.status),
            created_at=doc.creation,
        )

    @staticmethod
    def _priority_to_frappe(priority: TaskPriority) -> str:
        return {
            TaskPriority.HIGH: "High",
            TaskPriority.MEDIUM: "Medium",
            TaskPriority.LOW: "Low",
            TaskPriority.URGENT: "High",
        }.get(priority, "Medium")

    @staticmethod
    def _priority_from_frappe(
        priority: str | None,
    ) -> TaskPriority:
        return {
            "High": TaskPriority.HIGH,
            "Medium": TaskPriority.MEDIUM,
            "Low": TaskPriority.LOW,
        }.get(
            priority or "Medium",
            TaskPriority.MEDIUM,
        )

    @staticmethod
    def _status_to_frappe(status: TaskStatus) -> str:
        return {
            TaskStatus.OPEN: "Open",
            TaskStatus.IN_PROGRESS: "Open",
            TaskStatus.COMPLETED: "Closed",
            TaskStatus.CANCELLED: "Cancelled",
        }.get(status, "Open")

    @staticmethod
    def _status_from_frappe(
        status: str | None,
    ) -> TaskStatus:
        return {
            "Open": TaskStatus.OPEN,
            "Closed": TaskStatus.COMPLETED,
            "Cancelled": TaskStatus.CANCELLED,
        }.get(
            status or "Open",
            TaskStatus.OPEN,
        )

    # =====================================================
    # CRUD
    # =====================================================

    def save(self, entity: CRMTask) -> CRMTask:
        tenant_id = self._validate_tenant(entity)

        name = frappe.db.get_value(
            self.DOCTYPE,
            {
                self.ID_FIELD: entity.task_id,
                self.TENANT_FIELD: tenant_id,
            },
            "name",
        )

        if name:
            doc = frappe.get_doc(
                self.DOCTYPE,
                name,
            )
        else:
            doc = frappe.new_doc(
                self.DOCTYPE,
            )

        doc.set(
            self.ID_FIELD,
            entity.task_id,
        )

        doc.set(
            self.TENANT_FIELD,
            tenant_id,
        )

        doc.set(
            self.TITLE_FIELD,
            entity.title,
        )

        doc.set(
            "reference_type",
            entity.related_type,
        )

        doc.set(
            "reference_name",
            entity.related_id,
        )

        doc.set(
            "description",
            entity.description,
        )

        doc.set(
            "allocated_to",
            entity.assigned_to,
        )

        doc.set(
            "date",
            entity.due_date,
        )

        doc.set(
            "priority",
            self._priority_to_frappe(
                entity.priority,
            ),
        )

        doc.set(
            "status",
            self._status_to_frappe(
                entity.status,
            ),
        )

        doc.save(
            ignore_permissions=True,
        )

        frappe.db.commit()

        return self._to_model(doc)

    def get(
        self,
        entity_id: str,
    ) -> CRMTask | None:

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

    def list(self) -> list[CRMTask]:

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
    ) -> list[CRMTask]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                "reference_type": related_type,
                "reference_name": related_id,
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

    def find_by_status(
        self,
        status: TaskStatus,
    ) -> list[CRMTask]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                "status": self._status_to_frappe(status),
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

    def find_by_assignee(
        self,
        assigned_to: str,
    ) -> list[CRMTask]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                "allocated_to": assigned_to,
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

    def due(self) -> list[CRMTask]:

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
                "status": "Open",
                "date": ["<=", date.today()],
            },
            fields=["name"],
            order_by="date asc",
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
    ) -> list[CRMTask]:

        query = (query or "").strip()

        if not query:
            return self.list()

        tenant_id = self._tenant_id()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                self.TENANT_FIELD: tenant_id,
            },
            or_filters=[
                [
                    self.DOCTYPE,
                    self.TITLE_FIELD,
                    "like",
                    f"%{query}%",
                ],
                [
                    self.DOCTYPE,
                    "description",
                    "like",
                    f"%{query}%",
                ],
                [
                    self.DOCTYPE,
                    "allocated_to",
                    "like",
                    f"%{query}%",
                ],
            ],
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
