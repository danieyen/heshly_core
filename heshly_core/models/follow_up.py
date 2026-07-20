from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FollowUpType(str, Enum):

    CALL = "call"

    WHATSAPP = "whatsapp"

    EMAIL = "email"

    MEETING = "meeting"

    TASK = "task"


class FollowUpStatus(str, Enum):

    PENDING = "pending"

    SCHEDULED = "scheduled"

    COMPLETED = "completed"

    CANCELLED = "cancelled"

    MISSED = "missed"


@dataclass(slots=True)
class FollowUp:

    follow_up_id: str

    business_id: str

    related_type: str

    related_id: str

    follow_up_type: FollowUpType

    scheduled_for: datetime

    subject: str

    description: str | None = None

    assigned_to: str | None = None

    status: FollowUpStatus = (
        FollowUpStatus.PENDING
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )

    completed_at: datetime | None = None