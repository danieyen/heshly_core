from __future__ import annotations

import uuid
from datetime import datetime

import frappe

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpStatus,
    FollowUpType,
)


class ReminderSchedulerError(Exception):
    pass


class ReminderScheduler:

    DOCTYPE = "Follow Up"

    def __init__(self):
        pass

    def schedule(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        follow_up_type: FollowUpType,
        scheduled_for: datetime,
        subject: str,
        description: str | None = None,
        assigned_to: str | None = None,
    ) -> FollowUp:

        if not business_id:
            raise ReminderSchedulerError(
                "Business ID is required."
            )

        if scheduled_for <= datetime.utcnow():
            raise ReminderSchedulerError(
                "Scheduled time must be in the future."
            )

        follow_up = FollowUp(
            follow_up_id=self._generate_id(),
            business_id=business_id,
            related_type=related_type,
            related_id=related_id,
            follow_up_type=follow_up_type,
            scheduled_for=scheduled_for,
            subject=subject,
            description=description,
            assigned_to=assigned_to,
            status=FollowUpStatus.PENDING,
        )

        doc = frappe.new_doc(self.DOCTYPE)

        doc.follow_up_id = follow_up.follow_up_id
        doc.business_id = follow_up.business_id
        doc.related_type = follow_up.related_type
        doc.related_id = follow_up.related_id
        doc.follow_up_type = follow_up.follow_up_type.value
        doc.scheduled_for = follow_up.scheduled_for
        doc.subject = follow_up.subject
        doc.description = follow_up.description
        doc.assigned_to = follow_up.assigned_to
        doc.status = follow_up.status.value
        doc.completed_at = follow_up.completed_at

        doc.insert(ignore_permissions=True)

        frappe.db.commit()

        return self._to_model(doc)

    def due_reminders(
        self,
        current_time: datetime | None = None,
    ) -> list[FollowUp]:

        if current_time is None:
            current_time = datetime.utcnow()

        rows = frappe.get_all(
            self.DOCTYPE,
            filters={
                "status": FollowUpStatus.PENDING.value,
                "scheduled_for": ["<=", current_time],
            },
            fields=[
                "follow_up_id",
                "business_id",
                "related_type",
                "related_id",
                "follow_up_type",
                "scheduled_for",
                "subject",
                "description",
                "assigned_to",
                "status",
                "creation",
                "completed_at",
            ],
            order_by="scheduled_for asc",
        )

        return [
            self._row_to_model(row)
            for row in rows
        ]

    def overdue(
        self,
        current_time: datetime | None = None,
    ) -> list[FollowUp]:

        return self.due_reminders(current_time)

    def complete(
        self,
        follow_up_id: str,
    ) -> FollowUp:

        name = frappe.db.get_value(
            self.DOCTYPE,
            {"follow_up_id": follow_up_id},
            "name",
        )

        if not name:
            raise ReminderSchedulerError(
                "Follow-up not found."
            )

        completed_at = datetime.utcnow()

        frappe.db.set_value(
            self.DOCTYPE,
            name,
            {
                "status": FollowUpStatus.COMPLETED.value,
                "completed_at": completed_at,
            },
        )

        frappe.db.commit()

        doc = frappe.get_doc(
            self.DOCTYPE,
            name,
        )

        return self._to_model(doc)

    def get(
        self,
        follow_up_id: str,
    ) -> FollowUp | None:

        name = frappe.db.get_value(
            self.DOCTYPE,
            {"follow_up_id": follow_up_id},
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

    def _to_model(
        self,
        doc,
    ) -> FollowUp:

        return FollowUp(
            follow_up_id=doc.follow_up_id,
            business_id=doc.business_id,
            related_type=doc.related_type or "",
            related_id=doc.related_id or "",
            follow_up_type=FollowUpType(
                doc.follow_up_type
            ),
            scheduled_for=doc.scheduled_for,
            subject=doc.subject,
            description=doc.description,
            assigned_to=doc.assigned_to,
            status=FollowUpStatus(
                doc.status
            ),
            created_at=doc.creation,
            completed_at=doc.completed_at,
        )

    def _row_to_model(
        self,
        row,
    ) -> FollowUp:

        return FollowUp(
            follow_up_id=row["follow_up_id"],
            business_id=row["business_id"],
            related_type=row.get("related_type") or "",
            related_id=row.get("related_id") or "",
            follow_up_type=FollowUpType(
                row["follow_up_type"]
            ),
            scheduled_for=row["scheduled_for"],
            subject=row["subject"],
            description=row.get("description"),
            assigned_to=row.get("assigned_to"),
            status=FollowUpStatus(
                row["status"]
            ),
            created_at=row.get("creation"),
            completed_at=row.get("completed_at"),
        )

    def _generate_id(self) -> str:

        return f"FU-{uuid.uuid4().hex[:8].upper()}"
