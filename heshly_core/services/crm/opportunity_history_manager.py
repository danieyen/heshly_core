from __future__ import annotations

from datetime import datetime
import uuid

from heshly_core.models.opportunity import (
    OpportunityActivity,
    OpportunityActivityType,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class OpportunityHistoryError(Exception):
    pass


class OpportunityHistoryManager:
    """
    Tenant-aware opportunity activity history manager.

    Every activity is associated with the active tenant.
    History reads are restricted to that tenant.
    """

    def __init__(self):
        self.activities: list[OpportunityActivity] = []
        self.context = TenantContext()

    # =====================================================
    # Tenant
    # =====================================================

    def _current_tenant(self) -> str:

        tenant_id = self.context.get()

        if not tenant_id:
            raise OpportunityHistoryError(
                "Active tenant context is required."
            )

        return tenant_id

    # =====================================================
    # Add Activity
    # =====================================================

    def add_activity(
        self,
        opportunity_id: str,
        activity_type: OpportunityActivityType,
        description: str,
        created_by: str | None = None,
    ) -> OpportunityActivity:

        if not opportunity_id:
            raise OpportunityHistoryError(
                "Opportunity ID is required."
            )

        if not description:
            raise OpportunityHistoryError(
                "Activity description is required."
            )

        tenant_id = self._current_tenant()

        activity = OpportunityActivity(
            activity_id=self._generate_id(),
            opportunity_id=opportunity_id,
            tenant_id=tenant_id,
            activity_type=activity_type,
            description=description,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )

        self.activities.append(activity)

        return activity

    # =====================================================
    # History
    # =====================================================

    def get_history(
        self,
        opportunity_id: str,
    ) -> list[OpportunityActivity]:

        tenant_id = self._current_tenant()

        return [
            activity
            for activity in self.activities
            if (
                activity.tenant_id == tenant_id
                and activity.opportunity_id == opportunity_id
            )
        ]

    # =====================================================
    # Utilities
    # =====================================================

    def clear(self) -> None:

        tenant_id = self._current_tenant()

        self.activities = [
            activity
            for activity in self.activities
            if activity.tenant_id != tenant_id
        ]

    def count(self) -> int:

        tenant_id = self._current_tenant()

        return sum(
            1
            for activity in self.activities
            if activity.tenant_id == tenant_id
        )

    def _generate_id(self) -> str:

        return f"ACT-{uuid.uuid4().hex[:8].upper()}"
