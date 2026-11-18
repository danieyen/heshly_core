from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum

from heshly_core.models.calendar import CalendarProvider, CalendarConfiguration
from heshly_core.models.calendar_provider import ProviderConnection


class CalendarConnectionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ERROR = "error"


@dataclass(slots=True)
class CalendarConnection:
    """
    Tenant-scoped calendar connection domain model.
    OAuth tokens are owned by Heshly Core, NOT n8n.
    business_name is display-only.
    """

    connection_id: str
    tenant_id: str
    provider: CalendarProvider
    calendar_id: str
    timezone: str = "Africa/Nairobi"
    status: CalendarConnectionStatus = CalendarConnectionStatus.ACTIVE
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: datetime | None = None
    connected_at: datetime | None = None
    last_sync_at: datetime | None = None
    business_name: str = ""
    settings: dict = field(default_factory=dict)

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        now = now or datetime.now(UTC)
        # normalize to aware
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return now >= exp

    def to_provider_connection(self) -> ProviderConnection:
        """
        Convert to runtime ProviderConnection + CalendarConfiguration.
        """
        config = CalendarConfiguration(
            provider=self.provider,
            calendar_id=self.calendar_id,
            timezone=self.timezone,
            tenant_id=self.tenant_id,
            business_name=self.business_name or "",
            settings=dict(self.settings) if self.settings else {},
        )
        return ProviderConnection(
            configuration=config,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires_at=self.expires_at,
        )

    @classmethod
    def from_provider_connection(
        cls,
        connection_id: str,
        connection: ProviderConnection,
        status: CalendarConnectionStatus | str = CalendarConnectionStatus.ACTIVE,
    ) -> "CalendarConnection":
        if isinstance(status, str):
            try:
                status = CalendarConnectionStatus(status)
            except ValueError:
                status = CalendarConnectionStatus.ACTIVE
        cfg = connection.configuration
        return cls(
            connection_id=connection_id,
            tenant_id=cfg.tenant_id,
            provider=cfg.provider,
            calendar_id=cfg.calendar_id,
            timezone=cfg.timezone,
            status=status,
            access_token=connection.access_token,
            refresh_token=connection.refresh_token,
            expires_at=connection.expires_at,
            business_name=cfg.business_name or "",
            settings=dict(cfg.settings) if cfg.settings else {},
        )
