from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.models.calendar_provider import ProviderConnection
from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
from heshly_core.services.tenant.tenant_context import TenantContext


def _normalize_provider(provider: CalendarProvider | str) -> CalendarProvider:
    if isinstance(provider, CalendarProvider):
        return provider
    try:
        return CalendarProvider(str(provider).lower())
    except ValueError:
        return CalendarProvider.CUSTOM


class CalendarConnectionService:
    """
    Domain service for tenant-scoped calendar connections.
    Persistence is owned by Heshly Core (DocType: Heshly Calendar Connection).
    OAuth tokens must never be delegated to n8n.
    """

    def __init__(
        self,
        repository: CalendarConnectionRepository | None = None,
        tenant_context: TenantContext | None = None,
    ) -> None:
        self.repository = repository or CalendarConnectionRepository()
        self.tenant_context = tenant_context or TenantContext()

    def _require_tenant(self, tenant_id: str | None = None) -> str:
        if tenant_id is not None:
            # validate against context; repository will enforce match
            return self.repository.require_tenant(tenant_id)
        return self.tenant_context.require()

    def save(self, connection: CalendarConnection) -> CalendarConnection:
        """
        Create or update a tenant-scoped connection.
        Tenant is always derived from TenantContext (canonical).
        business_name is persisted as display-only.
        """
        tenant_id = self._require_tenant(connection.tenant_id)
        if connection.tenant_id != tenant_id:
            raise PermissionError("Calendar connection tenant mismatch.")
        # normalize
        connection.provider = _normalize_provider(connection.provider)
        if isinstance(connection.status, str):
            try:
                connection.status = CalendarConnectionStatus(connection.status)
            except ValueError:
                connection.status = CalendarConnectionStatus.ACTIVE
        if not connection.connected_at:
            connection.connected_at = datetime.now(UTC)
        return self.repository.save(connection)

    def save_provider_connection(
        self,
        connection_id: str,
        provider_connection: ProviderConnection,
        status: CalendarConnectionStatus | str = CalendarConnectionStatus.ACTIVE,
    ) -> CalendarConnection:
        tenant_id = self._require_tenant(provider_connection.configuration.tenant_id)
        model = CalendarConnection.from_provider_connection(
            connection_id=connection_id,
            connection=provider_connection,
            status=status,
        )
        # enforce canonical tenant
        model.tenant_id = tenant_id
        return self.save(model)

    def get(self, connection_id: str, tenant_id: str | None = None) -> CalendarConnection | None:
        tid = self._require_tenant(tenant_id)
        return self.repository.get(connection_id, tenant_id=tid)

    def list(self, tenant_id: str | None = None) -> list[CalendarConnection]:
        tid = self._require_tenant(tenant_id)
        return self.repository.list(tenant_id=tid)

    def delete(self, connection_id: str, tenant_id: str | None = None) -> bool:
        tid = self._require_tenant(tenant_id)
        return self.repository.delete(connection_id, tenant_id=tid)

    def get_provider_connection(
        self, connection_id: str, tenant_id: str | None = None
    ) -> ProviderConnection | None:
        tid = self._require_tenant(tenant_id)
        return self.repository.to_provider_connection(connection_id, tenant_id=tid)

    def update_tokens(
        self,
        connection_id: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        tenant_id: str | None = None,
    ) -> CalendarConnection | None:
        tid = self._require_tenant(tenant_id)
        return self.repository.update_tokens(
            connection_id, access_token=access_token, refresh_token=refresh_token, expires_at=expires_at, tenant_id=tid
        )

    def set_status(
        self, connection_id: str, status: CalendarConnectionStatus | str, tenant_id: str | None = None
    ) -> CalendarConnection | None:
        tid = self._require_tenant(tenant_id)
        existing = self.repository.get(connection_id, tenant_id=tid)
        if not existing:
            return None
        if isinstance(status, str):
            try:
                status = CalendarConnectionStatus(status)
            except ValueError:
                status = CalendarConnectionStatus.ACTIVE
        existing.status = status
        return self.repository.save(existing)
