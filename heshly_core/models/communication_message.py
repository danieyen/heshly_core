from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from heshly_core.models.channel_route import (
    CommunicationChannel,
)


@dataclass(slots=True)
class CommunicationMessage:
    """
    Communication Message.
    """

    message_id: str

    tenant_id: str

    recipient: str

    subject: str = ""

    body: str = ""

    channel: CommunicationChannel | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )