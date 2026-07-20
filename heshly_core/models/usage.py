from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class UsageMetric(str, Enum):
    """
    Tenant usage categories.
    """

    MESSAGES_SENT = "messages_sent"

    AI_CONVERSATIONS = "ai_conversations"

    APPOINTMENTS_BOOKED = "appointments_booked"

    LEADS_GENERATED = "leads_generated"


@dataclass(slots=True)
class TenantUsage:
    """
    Tracks tenant consumption.
    """

    usage_id: str

    tenant_id: str

    metric: UsageMetric

    quantity: int = 0

    period: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    def increment(
        self,
        amount: int = 1,
    ):

        self.quantity += amount

        self.updated_at = datetime.now(UTC)