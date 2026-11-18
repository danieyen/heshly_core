from __future__ import annotations

from dataclasses import dataclass

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


@dataclass(slots=True)
class AppointmentAnalytics:
    total: int
    open: int
    unverified: int
    closed: int


class AppointmentAnalyticsService:

    DOCTYPE = "Appointment"
    TENANT_FIELD = "custom_heshly_tenant_id"

    def get(self) -> AppointmentAnalytics:
        tenant_id = TenantContext().require()

        base_filters = {
            self.TENANT_FIELD: tenant_id,
        }

        total = frappe.db.count(
            self.DOCTYPE,
            filters=base_filters,
        )

        open_count = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "status": "Open",
            },
        )

        unverified = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "status": "Unverified",
            },
        )

        closed = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "status": "Closed",
            },
        )

        return AppointmentAnalytics(
            total=total,
            open=open_count,
            unverified=unverified,
            closed=closed,
        )
