from __future__ import annotations

from datetime import datetime
from typing import Any

from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.services.calendar.calendar_connection_service import CalendarConnectionService
from heshly_core.services.tenant.tenant_context import TenantContext


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


class CalendarConnectionAPI:
    """
    Thin API layer for Heshly Core-owned calendar connections.
    Resolves tenant_id from TenantContext (canonical); never from business_name.
    """

    def __init__(self, tenant_context: TenantContext | None = None, service: CalendarConnectionService | None = None):
        self.tenant_context = tenant_context or TenantContext()
        self.service = service or CalendarConnectionService(tenant_context=self.tenant_context)

    def _require_tenant(self, payload: dict | None = None) -> str:
        # Tenant must be in context (set by before_request / auth). Allow override from payload only if context already set and matches.
        tenant_id = None
        if isinstance(payload, dict):
            tenant_id = payload.get("tenant_id") or payload.get("tenantId")
        if tenant_id:
            try:
                # validate matches context when context exists
                ctx = self.tenant_context.get()
                if ctx and str(ctx) != str(tenant_id).strip():
                    # cross-tenant attempt
                    raise PermissionError("Tenant mismatch.")
                self.tenant_context.set(tenant_id)
            except ValueError:
                raise
            except PermissionError:
                raise
            except Exception:
                pass
        return self.tenant_context.require()

    def save(self, payload: Any) -> dict:
        data = payload if isinstance(payload, dict) else {}
        tenant_id = self._require_tenant(data)
        try:
            provider = CalendarProvider(str(data.get("provider") or "erpnext").lower())
        except ValueError:
            provider = CalendarProvider.CUSTOM
        status_raw = data.get("status") or "active"
        try:
            status = CalendarConnectionStatus(str(status_raw).lower())
        except ValueError:
            status = CalendarConnectionStatus.ACTIVE
        connection = CalendarConnection(
            connection_id=str(data.get("connection_id") or data.get("connectionId") or f"{tenant_id}:{provider.value}:{data.get('calendar_id') or 'default'}"),
            tenant_id=tenant_id,
            provider=provider,
            calendar_id=str(data.get("calendar_id") or "default"),
            timezone=str(data.get("timezone") or "Africa/Nairobi"),
            status=status,
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            expires_at=_parse_dt(data.get("expires_at")),
            business_name=str(data.get("business_name") or ""),
            settings=data.get("settings") if isinstance(data.get("settings"), dict) else {},
        )
        saved = self.service.save(connection)
        return {"success": True, "connection": {"connection_id": saved.connection_id, "tenant_id": saved.tenant_id, "provider": saved.provider.value, "calendar_id": saved.calendar_id, "timezone": saved.timezone, "status": saved.status.value, "expires_at": saved.expires_at.isoformat() if saved.expires_at else None}}

    def get(self, payload: Any) -> dict:
        data = payload if isinstance(payload, dict) else {}
        tenant_id = self._require_tenant(data)
        cid = str(data.get("connection_id") or data.get("connectionId") or "")
        if not cid:
            return {"success": False, "message": "connection_id required"}
        model = self.service.get(cid, tenant_id=tenant_id)
        if not model:
            return {"success": False, "message": "Not found"}
        return {"success": True, "connection": {"connection_id": model.connection_id, "tenant_id": model.tenant_id, "provider": model.provider.value, "calendar_id": model.calendar_id, "timezone": model.timezone, "status": model.status.value, "expires_at": model.expires_at.isoformat() if model.expires_at else None, "business_name": model.business_name}}

    def list(self, payload: Any = None) -> dict:
        data = payload if isinstance(payload, dict) else {}
        tenant_id = self._require_tenant(data)
        items = self.service.list(tenant_id=tenant_id)
        return {"success": True, "connections": [{"connection_id": c.connection_id, "tenant_id": c.tenant_id, "provider": c.provider.value, "calendar_id": c.calendar_id, "timezone": c.timezone, "status": c.status.value, "expires_at": c.expires_at.isoformat() if c.expires_at else None, "has_access_token": bool(c.access_token), "has_refresh_token": bool(c.refresh_token)} for c in items]}

    def delete(self, payload: Any) -> dict:
        data = payload if isinstance(payload, dict) else {}
        tenant_id = self._require_tenant(data)
        cid = str(data.get("connection_id") or data.get("connectionId") or "")
        if not cid:
            return {"success": False, "message": "connection_id required"}
        ok = self.service.delete(cid, tenant_id=tenant_id)
        return {"success": bool(ok)}

    def health(self) -> dict:
        return {"api": "calendar_connection_api", "status": "healthy"}
