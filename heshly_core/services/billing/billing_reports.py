from __future__ import annotations

from heshly_core.models.usage import (
    UsageMetric,
)

from heshly_core.repositories.usage_repository import (
    UsageRepository,
)

from heshly_core.services.billing.usage_calculator import (
    UsageCalculator,
)


class BillingReports:
    """
    Generates billing and usage reports.
    """

    def __init__(
        self,
        repository: UsageRepository | None = None,
    ):

        self.repository = (
            repository
            or UsageRepository()
        )

        self.calculator = UsageCalculator()

        self.calculator.repository = (
            self.repository
        )


    # =====================================================
    # Tenant Usage Report
    # =====================================================

    def tenant_report(
        self,
        tenant_id: str,
    ):

        return {

            "tenant_id":
                tenant_id,

            "messages_sent":
                self.calculator.calculate_metric(
                    tenant_id,
                    UsageMetric.MESSAGES_SENT,
                ),

            "ai_conversations":
                self.calculator.calculate_metric(
                    tenant_id,
                    UsageMetric.AI_CONVERSATIONS,
                ),

            "appointments_booked":
                self.calculator.calculate_metric(
                    tenant_id,
                    UsageMetric.APPOINTMENTS_BOOKED,
                ),

            "leads_generated":
                self.calculator.calculate_metric(
                    tenant_id,
                    UsageMetric.LEADS_GENERATED,
                ),

        }


    def all_tenants_report(self):

        tenants = set(

            usage.tenant_id

            for usage in self.repository.list()

        )

        return [

            self.tenant_report(
                tenant_id
            )

            for tenant_id in tenants

        ]


    def usage_events_count(self):

        return self.repository.count()


    def health(self):

        return {

            "service":
                "billing_reports",

            "status":
                "healthy",

        }