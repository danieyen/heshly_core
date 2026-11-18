from __future__ import annotations

from datetime import datetime, UTC, timedelta
from typing import Tuple

from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_connection import CalendarConnection
from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.google.google_oauth_service import GoogleOAuthService

# Refresh proactively if expiring within this window
REFRESH_SKEW_SECONDS = 120


def _is_expired_or_near_expiry(conn: CalendarConnection, skew_seconds: int = REFRESH_SKEW_SECONDS) -> bool:
    if not conn.expires_at:
        return False
    exp = conn.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    return now + timedelta(seconds=skew_seconds) >= exp


def get_valid_access_token(tenant_id: str | None = None, *, repository: CalendarConnectionRepository | None = None) -> Tuple[str, CalendarConnection]:
    """
    Retrieve a valid access token for this tenant's Google connection.

    - Resolves tenant_id from TenantContext if not supplied (canonical)
    - Loads connection via repository (tenant-scoped)
    - If expired/near-expiry and refresh_token present, refreshes via GoogleOAuthService and persists
    - Raises clean domain errors (no secrets in message)

    Returns (access_token, connection)
    """
    ctx = TenantContext()
    if tenant_id is None:
        tenant_id = ctx.require()
    else:
        tenant_id = str(tenant_id).strip()
        # Enforce match with context when context exists
        current = ctx.get()
        if current is not None and current != tenant_id:
            raise PermissionError(f"Access denied to tenant '{tenant_id}'")

    repo = repository or CalendarConnectionRepository()
    conn = repo.get_for_provider(CalendarProvider.GOOGLE, tenant_id=tenant_id)
    if not conn:
        raise RuntimeError("No Google Calendar connection found for this tenant. Please connect Google Calendar first.")
    if not conn.access_token:
        # No access token but maybe refresh_token — try refresh
        if not conn.refresh_token:
            raise RuntimeError("Google Calendar connection has no access token and no refresh token. Please reconnect Google Calendar.")

    # Need refresh?
    needs_refresh = _is_expired_or_near_expiry(conn) or not conn.access_token

    if needs_refresh:
        if not conn.refresh_token:
            # Mark expired, require re-auth (do not leak tokens)
            try:
                from heshly_core.models.calendar_connection import CalendarConnectionStatus

                conn.status = CalendarConnectionStatus.EXPIRED
                repo.save(conn)
            except Exception:
                pass
            raise RuntimeError("Google access token expired and no refresh token available. Please reconnect Google Calendar.")

        oauth = GoogleOAuthService()
        try:
            refreshed = oauth.refresh_access_token(conn.refresh_token)
        except RuntimeError as e:
            # Refresh failed — may be revoked
            msg = str(e)
            # Map common Google errors to actionable domain message without leaking token
            lowered = msg.lower()
            if "invalid_grant" in lowered or "revoked" in lowered or "expired" in lowered:
                try:
                    from heshly_core.models.calendar_connection import CalendarConnectionStatus

                    conn.status = CalendarConnectionStatus.EXPIRED
                    repo.save(conn)
                except Exception:
                    pass
                raise RuntimeError("Google authorization has been revoked or expired. Please reconnect Google Calendar.") from e
            raise RuntimeError(f"Failed to refresh Google access token: {msg[:200]}") from e

        new_access = refreshed.get("access_token")
        new_refresh = refreshed.get("refresh_token") or conn.refresh_token
        new_expires_at = refreshed.get("expires_at")

        if not new_access:
            raise RuntimeError("Google token refresh did not return an access token")

        # Persist refreshed tokens (encrypted)
        updated = repo.update_tokens(
            conn.connection_id,
            access_token=new_access,
            refresh_token=new_refresh,
            expires_at=new_expires_at,
            tenant_id=tenant_id,
        )
        if updated is not None:
            conn = updated
        else:
            # fallback: mutate in-memory
            conn.access_token = new_access
            conn.refresh_token = new_refresh
            conn.expires_at = new_expires_at

    if not conn.access_token:
        raise RuntimeError("Google Calendar connection has no valid access token after refresh. Please reconnect.")

    return conn.access_token, conn
