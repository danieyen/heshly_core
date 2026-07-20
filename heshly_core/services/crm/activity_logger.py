from __future__ import annotations

import uuid
from datetime import datetime

from heshly_core.models.activity import (
    Activity,
    ActivityStatus,
    ActivityPriority,
)



class ActivityLoggingError(Exception):
    pass



class ActivityLogger:
    """
    Creates and stores CRM activity logs.
    """


    def __init__(self):

        self.activities: list[Activity] = []



    def log(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        activity_type: str,
        subject: str,
        description: str | None = None,
        assigned_to: str | None = None,
        priority: ActivityPriority = (
            ActivityPriority.MEDIUM
        ),
    ) -> Activity:


        if not business_id:

            raise ActivityLoggingError(
                "Business ID is required."
            )


        if not related_id:

            raise ActivityLoggingError(
                "Related ID is required."
            )


        if not subject:

            raise ActivityLoggingError(
                "Activity subject is required."
            )


        activity = Activity(

            activity_id=self._generate_id(),

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            activity_type=activity_type,

            subject=subject,

            description=description,

            assigned_to=assigned_to,

            priority=priority,

        )


        self.activities.append(activity)


        return activity



    def get_history(
        self,
        related_type: str,
        related_id: str,
    ) -> list[Activity]:


        return [

            activity

            for activity in self.activities

            if (
                activity.related_type
                == related_type

                and

                activity.related_id
                == related_id
            )

        ]



    def _generate_id(self):

        return (
            f"ACT-{uuid.uuid4().hex[:8].upper()}"
        )