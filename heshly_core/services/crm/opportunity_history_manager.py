from __future__ import annotations

from datetime import datetime
import uuid

from heshly_core.models.opportunity import (
    OpportunityActivity,
    OpportunityActivityType,
)


class OpportunityHistoryError(Exception):
    pass


class OpportunityHistoryManager:
    """
    Manages opportunity activity history.
    """


    def __init__(self):

        self.activities: list[
            OpportunityActivity
        ] = []


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


        activity = OpportunityActivity(
            activity_id=self._generate_id(),
            opportunity_id=opportunity_id,
            activity_type=activity_type,
            description=description,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )


        self.activities.append(activity)

        return activity



    def get_history(
        self,
        opportunity_id: str,
    ) -> list[OpportunityActivity]:


        return [
            activity
            for activity in self.activities
            if activity.opportunity_id
            == opportunity_id
        ]



    def _generate_id(self):

        return (
            f"ACT-{uuid.uuid4().hex[:8].upper()}"
        )