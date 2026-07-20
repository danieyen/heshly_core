from __future__ import annotations

from heshly_core.models.usage import (
    UsageMetric,
)

from heshly_core.repositories.usage_repository import (
    UsageRepository,
)


class UsageCalculator:
    """
    Calculates tenant usage totals.
    """

    def __init__(self):

        self.repository = (
            UsageRepository()
        )


    # =====================================================
    # Calculate Metric
    # =====================================================

    def calculate_metric(
        self,
        tenant_id: str,
        metric: UsageMetric,
    ) -> int:

        records = (
            self.repository.list_by_tenant(
                tenant_id
            )
        )

        return sum(

            record.quantity

            for record in records

            if record.metric == metric

        )


    # =====================================================
    # Messages
    # =====================================================

    def messages_sent(
        self,
        tenant_id: str,
    ) -> int:

        return self.calculate_metric(

            tenant_id,

            UsageMetric.MESSAGES_SENT,

        )


    # =====================================================
    # AI Conversations
    # =====================================================

    def ai_conversations(
        self,
        tenant_id: str,
    ) -> int:

        return self.calculate_metric(

            tenant_id,

            UsageMetric.AI_CONVERSATIONS,

        )


    # =====================================================
    # Appointments
    # =====================================================

    def appointments_booked(
        self,
        tenant_id: str,
    ) -> int:

        return self.calculate_metric(

            tenant_id,

            UsageMetric.APPOINTMENTS_BOOKED,

        )


    # =====================================================
    # Leads
    # =====================================================

    def leads_generated(
        self,
        tenant_id: str,
    ) -> int:

        return self.calculate_metric(

            tenant_id,

            UsageMetric.LEADS_GENERATED,

        )


    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        tenant_id: str,
    ):

        return {

            "tenant_id":
                tenant_id,

            "messages_sent":
                self.messages_sent(
                    tenant_id
                ),

            "ai_conversations":
                self.ai_conversations(
                    tenant_id
                ),

            "appointments_booked":
                self.appointments_booked(
                    tenant_id
                ),

            "leads_generated":
                self.leads_generated(
                    tenant_id
                ),

        }


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "usage_calculator",

            "status":
                "healthy",

        }