from __future__ import annotations

from dataclasses import dataclass

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


@dataclass(slots=True)
class OpportunityAnalytics:
    total: int
    open: int
    won: int
    lost: int
    pipeline_value: float
    weighted_pipeline_value: float


class OpportunityAnalyticsService:

    DOCTYPE = "Opportunity"
    TENANT_FIELD = "custom_heshly_tenant_id"

    def get(self) -> OpportunityAnalytics:
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

        won = frappe.db.count(
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
                "status": "Lost",
            },
        )

        rows = frappe.get_all(
            self.DOCTYPE,
            filters=base_filters,
            fields=[
                "opportunity_amount",
                "probability",
                "status",
            ],
        )

        pipeline_value = 0.0
        weighted_pipeline_value = 0.0

        for row in rows:
            amount = float(row.opportunity_amount or 0)
            probability = float(row.probability or 0)

            if row.status == "Open":
                pipeline_value += amount
                weighted_pipeline_value += (
                    amount * probability / 100
                )

        return OpportunityAnalytics(
            total=total,
            open=open_count,
            won=won,
            lost=lost,
            pipeline_value=round(pipeline_value, 2),
            weighted_pipeline_value=round(
                weighted_pipeline_value,
                2,
            ),
        )
