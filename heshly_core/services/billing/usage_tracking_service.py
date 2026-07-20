from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.usage import (
    TenantUsage,
    UsageMetric,
)

from heshly_core.repositories.usage_repository import (
    UsageRepository,
)


class UsageTrackingService:
    """
    Records tenant usage events.

    Central usage collection point
    for all Heshly modules.
    """

    def __init__(self):

        self.repository = UsageRepository()


    # =====================================================
    # Track Generic Usage
    # =====================================================

    def track(
        self,
        tenant_id: str,
        metric: UsageMetric,
        quantity: int = 1,
    ) -> TenantUsage:

        usage = TenantUsage(

            usage_id=self._generate_id(),

            tenant_id=tenant_id,

            metric=metric,

            quantity=quantity,

            period=datetime.now(
                UTC
            ).strftime("%Y-%m"),

        )

        return self.repository.save(
            usage
        )


    # =====================================================
    # Messages
    # =====================================================

    def track_message(
        self,
        tenant_id: str,
        quantity: int = 1,
    ):

        return self.track(

            tenant_id,

            UsageMetric.MESSAGES_SENT,

            quantity,

        )


    # =====================================================
    # AI Conversations
    # =====================================================

    def track_ai_conversation(
        self,
        tenant_id: str,
        quantity: int = 1,
    ):

        return self.track(

            tenant_id,

            UsageMetric.AI_CONVERSATIONS,

            quantity,

        )


    # =====================================================
    # Appointments
    # =====================================================

    def track_appointment(
        self,
        tenant_id: str,
        quantity: int = 1,
    ):

        return self.track(

            tenant_id,

            UsageMetric.APPOINTMENTS_BOOKED,

            quantity,

        )


    # =====================================================
    # Leads
    # =====================================================

    def track_lead(
        self,
        tenant_id: str,
        quantity: int = 1,
    ):

        return self.track(

            tenant_id,

            UsageMetric.LEADS_GENERATED,

            quantity,

        )


    # =====================================================
    # ID Generator
    # =====================================================

    def _generate_id(self):

        return (
            "usage_"
            +
            datetime.now(
                UTC
            ).strftime(
                "%Y%m%d%H%M%S%f"
            )
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "usage_tracking_service",

            "status":
                "healthy",

        }