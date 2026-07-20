from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ActivityStatus(str, Enum):

    PENDING = "pending"

    COMPLETED = "completed"

    CANCELLED = "cancelled"



class ActivityPriority(str, Enum):

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    URGENT = "urgent"



@dataclass(slots=True)
class Activity:

    activity_id: str

    business_id: str


    related_type: str
    related_id: str


    activity_type: str


    subject: str


    description: Optional[str] = None


    assigned_to: Optional[str] = None


    status: ActivityStatus = (
        ActivityStatus.PENDING
    )


    priority: ActivityPriority = (
        ActivityPriority.MEDIUM
    )


    due_date: Optional[datetime] = None


    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


    completed_at: Optional[datetime] = None