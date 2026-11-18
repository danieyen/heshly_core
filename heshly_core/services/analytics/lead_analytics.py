from __future__ import annotations

from dataclasses import dataclass

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


@dataclass(slots=True)
class LeadAnalytics:
    total: int
    new: int
    qualified: int
    converted: int
    lost: int
    conversion: float


class LeadAnalyticsService:

    DOCTYPE = "Lead"
    TENANT_FIELD = "custom_heshly_tenant_id"

    def get(self) -> LeadAnalytics:
        tenant_id = TenantContext().require()

        base_filters = {
            self.TENANT_FIELD: tenant_id,
        }

        total = frappe.db.count(
            self.DOCTYPE,
            filters=base_filters,
        )

        new = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "status": "Lead",
            },
        )

        qualified = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "qualification_status": "Qualified",
            },
        )

        converted = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "status": "Converted",
            },
        )

        lost = frappe.db.count(
            self.DOCTYPE,
            filters={
                **base_filters,
                "status": "Lost Quotation",
            },
        )

        conversion = (
            (converted / total) * 100
            if total
            else 0.0
        )

        return LeadAnalytics(
            total=total,
            new=new,
            qualified=qualified,
            converted=converted,
            lost=lost,
            conversion=round(conversion, 2),
        )
