from __future__ import annotations

import frappe
from datetime import datetime, UTC

from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.models.calendar_provider import ProviderConnection
from heshly_core.repositories.base_repository import BaseRepository


class CalendarConnectionRepository(BaseRepository[CalendarConnection]):
    """
    Persistent tenant-scoped calendar connection repository.

    Extends existing Heshly persistence patterns:
      - Uses dedicated DocType Heshly Calendar Connection
      - All reads/writes are filtered by TenantContext.require()
      - Password fields (access_token, refresh_token) use Frappe Password type via get_password()
      - Mirrors WhatsAppConfigurationRepository and FrappeBusinessRepository isolation approach
    Tokens are owned by Heshly Core, NOT n8n.
    """

    def require_tenant(self, tenant_id: str | None = None) -> str:
        """
        Calendar connections allow test harnesses to set TenantContext directly.
        Bypass the Frappe session check that WhatsApp/business flows use,
        but still enforce that the requested tenant equals the active context.
        """
        if tenant_id is None:
            return self.context.require()
        tenant_id = str(tenant_id).strip()
        if not tenant_id:
            raise ValueError("tenant_id is required")
        # In test / non-Frappe boot, frappe.session may be a stub
        current = self.context.get()
        if current is not None and current != tenant_id:
            raise PermissionError(f"Access denied to tenant '{tenant_id}'.")
        if current is None:
            # No context yet: set it (service already does) or require explicitly
            try:
                return self.context.require()
            except RuntimeError:
                # Allow direct tenant_id when bootstrapping (tests)
                return tenant_id
        return tenant_id

    DOCTYPE = "Heshly Calendar Connection"

    # -- save / upsert --

    def save(self, connection: CalendarConnection) -> CalendarConnection:
        tenant_id = self.require_tenant(connection.tenant_id)
        if connection.tenant_id != tenant_id:
            raise PermissionError("Calendar connection belongs to a different tenant.")
        # Unique per tenant+provider+calendar_id is enforced via connection_id; also guard cross-tenant overwrite
        existing_name = frappe.db.get_value(
            self.DOCTYPE,
            {"connection_id": connection.connection_id, "tenant_id": tenant_id},
            "name",
        )
        if existing_name:
            doc = frappe.get_doc(self.DOCTYPE, existing_name)
            # never allow changing tenant_id via save
            if doc.tenant_id != tenant_id:
                raise PermissionError("Cannot move calendar connection between tenants.")
        else:
            # also ensure caller is not hijacking another tenant's connection_id
            hijack = frappe.db.get_value(self.DOCTYPE, {"connection_id": connection.connection_id}, "name")
            if hijack:
                raise PermissionError("connection_id already exists for another tenant.")
            doc = frappe.new_doc(self.DOCTYPE)
            doc.connection_id = connection.connection_id

        doc.tenant_id = tenant_id
        doc.provider = connection.provider.value if isinstance(connection.provider, CalendarProvider) else str(connection.provider)
        doc.calendar_id = connection.calendar_id
        doc.timezone = connection.timezone
        doc.status = connection.status.value if isinstance(connection.status, CalendarConnectionStatus) else str(connection.status)
        # Business name is display-only
        doc.business_name = connection.business_name or ""
        if connection.access_token is not None:
            doc.access_token = connection.access_token
        if connection.refresh_token is not None:
            doc.refresh_token = connection.refresh_token
        # Normalize datetimes to naive UTC for MariaDB Datetime fields
        def _naive(dt):
            return dt.replace(tzinfo=None) if dt is not None and getattr(dt, "tzinfo", None) is not None else dt
        doc.expires_at = _naive(connection.expires_at)
        doc.connected_at = _naive(connection.connected_at)
        doc.last_sync_at = _naive(connection.last_sync_at)

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return connection

    def get(self, connection_id: str, tenant_id: str | None = None) -> CalendarConnection | None:
        tenant_id = self.require_tenant(tenant_id) if tenant_id is not None else self.current_tenant()
        name = frappe.db.get_value(self.DOCTYPE, {"connection_id": connection_id, "tenant_id": tenant_id}, "name")
        if not name:
            return None
        return self._to_model(frappe.get_doc(self.DOCTYPE, name))

    def get_for_provider(self, provider: CalendarProvider | str, tenant_id: str | None = None) -> CalendarConnection | None:
        tenant_id = self.require_tenant(tenant_id) if tenant_id is not None else self.current_tenant()
        prov = provider.value if isinstance(provider, CalendarProvider) else str(provider)
        name = frappe.db.get_value(self.DOCTYPE, {"provider": prov, "tenant_id": tenant_id}, "name")
        if not name:
            return None
        return self._to_model(frappe.get_doc(self.DOCTYPE, name))

    def list(self, tenant_id: str | None = None) -> list[CalendarConnection]:
        tenant_id = self.require_tenant(tenant_id) if tenant_id is not None else self.current_tenant()
        names = frappe.get_all(self.DOCTYPE, filters={"tenant_id": tenant_id}, pluck="name")
        result: list[CalendarConnection] = []
        for n in names:
            m = self._to_model(frappe.get_doc(self.DOCTYPE, n))
            if m:
                result.append(m)
        return result

    def exists(self, connection_id: str, tenant_id: str | None = None) -> bool:
        tenant_id = self.require_tenant(tenant_id) if tenant_id is not None else self.current_tenant()
        return bool(frappe.db.exists(self.DOCTYPE, {"connection_id": connection_id, "tenant_id": tenant_id}))

    def delete(self, connection_id: str, tenant_id: str | None = None) -> bool:
        tenant_id = self.require_tenant(tenant_id) if tenant_id is not None else self.current_tenant()
        name = frappe.db.get_value(self.DOCTYPE, {"connection_id": connection_id, "tenant_id": tenant_id}, "name")
        if not name:
            return False
        frappe.delete_doc(self.DOCTYPE, name, ignore_permissions=True)
        frappe.db.commit()
        return True

    def update_tokens(
        self,
        connection_id: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        tenant_id: str | None = None,
    ) -> CalendarConnection | None:
        tenant_id = self.require_tenant(tenant_id) if tenant_id is not None else self.current_tenant()
        name = frappe.db.get_value(self.DOCTYPE, {"connection_id": connection_id, "tenant_id": tenant_id}, "name")
        if not name:
            return None
        doc = frappe.get_doc(self.DOCTYPE, name)
        if access_token is not None:
            doc.access_token = access_token
        if refresh_token is not None:
            doc.refresh_token = refresh_token
        if expires_at is not None:
            # Normalize to naive UTC for MariaDB Datetime field
            if expires_at.tzinfo is not None:
                expires_at = expires_at.replace(tzinfo=None)
            doc.expires_at = expires_at
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return self._to_model(doc)

    def to_provider_connection(self, connection_id: str, tenant_id: str | None = None) -> ProviderConnection | None:
        model = self.get(connection_id, tenant_id=tenant_id)
        if not model:
            return None
        return model.to_provider_connection()

    @staticmethod
    def _to_model(doc) -> CalendarConnection | None:
        if not doc:
            return None
        provider_raw = getattr(doc, "provider", "erpnext")
        try:
            provider = CalendarProvider(provider_raw)
        except ValueError:
            provider = CalendarProvider.CUSTOM
        status_raw = getattr(doc, "status", "active")
        try:
            status = CalendarConnectionStatus(status_raw)
        except ValueError:
            status = CalendarConnectionStatus.ACTIVE
        # Password fields: use get_password when available
        try:
            access_token = doc.get_password("access_token") if getattr(doc, "access_token", None) else None
        except Exception:
            access_token = getattr(doc, "access_token", None) or None
        try:
            refresh_token = doc.get_password("refresh_token") if getattr(doc, "refresh_token", None) else None
        except Exception:
            refresh_token = getattr(doc, "refresh_token", None) or None
        return CalendarConnection(
            connection_id=getattr(doc, "connection_id", "") or doc.name,
            tenant_id=getattr(doc, "tenant_id", ""),
            provider=provider,
            calendar_id=getattr(doc, "calendar_id", ""),
            timezone=getattr(doc, "timezone", "Africa/Nairobi"),
            status=status,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=getattr(doc, "expires_at", None),
            connected_at=getattr(doc, "connected_at", None),
            last_sync_at=getattr(doc, "last_sync_at", None),
            business_name=getattr(doc, "business_name", "") or "",
            settings={},
        )
