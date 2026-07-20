from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class CommunicationChannel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"


@dataclass(slots=True)
class ChannelRoute:
    """
    Channel Routing Rule.
    """

    route_id: str

    tenant_id: str

    event: str

    preferred_channel: CommunicationChannel

    fallback_channels: list[CommunicationChannel] = field(
        default_factory=list
    )

    enabled: bool = True

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )