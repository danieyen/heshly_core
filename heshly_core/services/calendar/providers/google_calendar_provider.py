from __future__ import annotations

from datetime import datetime, UTC
from typing import Any
from urllib.parse import quote

import requests

from heshly_core.models.calendar import (
    AppointmentStatus,
    CalendarEvent,
)

from heshly_core.models.calendar_provider import (
    CalendarProviderStatus,
    ProviderAppointmentResult,
    ProviderConnection,
    ProviderEventQuery,
    ProviderEventsResult,
    ProviderHealth,
)

from heshly_core.services.calendar.providers.provider_interface import (
    CalendarProviderInterface,
)

from heshly_core.services.tenant.tenant_context import TenantContext

GOOGLE_CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"


def _parse_google_datetime(dt_obj: dict | None, tz_fallback: str = "UTC") -> datetime | None:
    """
    Parse Google Calendar event date/time.
    Handles:
      - {"dateTime": "2026-09-07T10:00:00+03:00"} (timed)
      - {"date": "2026-09-07"} (all-day)
    Returns UTC-aware datetime.
    """
    if not dt_obj or not isinstance(dt_obj, dict):
        return None
    date_time = dt_obj.get("dateTime")
    date_only = dt_obj.get("date")
    if date_time:
        try:
            # Google returns RFC3339; fromisoformat handles offset
            dt = datetime.fromisoformat(str(date_time).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except Exception:
            return None
    if date_only:
        try:
            # All-day: date is YYYY-MM-DD, treat as 00:00 in calendar timezone
            # Return as UTC midnight for normalization; provider preserves date
            dt = datetime.fromisoformat(str(date_only) + "T00:00:00+00:00")
            return dt
        except Exception:
            return None
    return None


def _is_all_day(start_obj: dict | None) -> bool:
    return bool(start_obj and "date" in start_obj and "dateTime" not in start_obj)


def _event_status_blocking(status: str | None) -> AppointmentStatus:
    # Google: confirmed, tentative, cancelled
    if status == "cancelled":
        return AppointmentStatus.CANCELLED
    return AppointmentStatus.CONFIRMED


class GoogleCalendarProvider(CalendarProviderInterface):
    """
    Real Google Calendar provider (Heshly Core-owned OAuth).

    Tenant-isolated: never stores a global singleton credential.
    Either:
      - Caller supplies ProviderConnection via connect() (ephemeral, e.g. tests), OR
      - Provider resolves the tenant's persisted connection via CalendarConnectionRepository + TokenService
        using TenantContext.require() (canonical tenant).

    Tokens are encrypted at rest (Password field) and refreshed automatically.
    """

    def __init__(self, repository=None) -> None:
        # Lazy import to avoid circular deps during module import
        self._connection: ProviderConnection | None = None
        self._repository = repository
        self._tenant_context = TenantContext()

    def _get_repository(self):
        if self._repository is not None:
            return self._repository
        from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
        self._repository = CalendarConnectionRepository()
        return self._repository

    def _resolve_token_and_calendar(self, calendar_id_hint: str | None = None) -> tuple[str, str, str]:
        """
        Resolve (access_token, calendar_id, tenant_id) for the current tenant.
        Prefers explicit _connection if present (test/ephemeral path), else loads from repository.
        Returns (access_token, calendar_id, tenant_id).
        Raises RuntimeError/PermissionError with clean messages (no secrets).
        """
        from heshly_core.services.google.google_calendar_token_service import get_valid_access_token

        # Ephemeral path: connect() was called with a ProviderConnection (e.g. unit tests)
        if self._connection is not None:
            cfg = self._connection.configuration
            # Validate tenant match with current context when available
            try:
                current = self._tenant_context.get()
                if current is not None and cfg.tenant_id != current:
                    raise PermissionError("Calendar provider tenant mismatch")
            except PermissionError:
                raise
            except Exception:
                pass
            # Token refresh for ephemeral path (if expired and refresh_token present)
            token = self._connection.access_token
            exp = self._connection.expires_at
            # If expired and we have refresh_token, try refresh inline
            if exp is not None:
                from datetime import timedelta
                exp_aware = exp if exp.tzinfo is not None else exp.replace(tzinfo=UTC)
                now = datetime.now(UTC)
                if now + timedelta(seconds=120) >= exp_aware and self._connection.refresh_token:
                    try:
                        from heshly_core.services.google.google_oauth_service import GoogleOAuthService
                        refreshed = GoogleOAuthService().refresh_access_token(self._connection.refresh_token)
                        new_at = refreshed.get("access_token")
                        new_exp = refreshed.get("expires_at")
                        new_rt = refreshed.get("refresh_token") or self._connection.refresh_token
                        if new_at:
                            self._connection.access_token = new_at
                            self._connection.refresh_token = new_rt
                            self._connection.expires_at = new_exp
                            # Persist if this connection corresponds to a stored record (best-effort)
                            try:
                                repo = self._get_repository()
                                cid = f"{cfg.tenant_id}:google:{cfg.calendar_id}"
                                repo.update_tokens(cid, access_token=new_at, refresh_token=new_rt, expires_at=new_exp, tenant_id=cfg.tenant_id)
                            except Exception:
                                pass
                            token = new_at
                    except Exception as e:
                        raise RuntimeError(f"Failed to refresh Google access token: {str(e)[:200]}") from e
            if not token:
                raise RuntimeError("Google Calendar connection has no access token. Reconnect Google Calendar.")
            cid = calendar_id_hint or cfg.calendar_id
            return token, cid, cfg.tenant_id

        # Persisted path: load from repository via TenantContext
        tenant_id = self._tenant_context.require()
        access_token, conn = get_valid_access_token(tenant_id, repository=self._get_repository())
        cal_id = calendar_id_hint or conn.calendar_id
        return access_token, cal_id, tenant_id

    def connect(self, connection: ProviderConnection) -> bool:
        self._connection = connection
        return True

    def disconnect(self) -> None:
        self._connection = None

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    def _handle_api_error(self, resp: requests.Response, action: str) -> None:
        # Map HTTP errors to domain errors without leaking tokens/headers
        if resp.status_code == 401:
            raise PermissionError("Google authorization expired or revoked (401). Please reconnect Google Calendar.")
        if resp.status_code == 403:
            raise PermissionError("Google Calendar access forbidden (403) — check scopes and sharing.")
        if resp.status_code == 404:
            raise RuntimeError(f"Google Calendar {action} failed: calendar or event not found (404). Check calendar_id.")
        try:
            body = resp.json()
            msg = body.get("error", {}).get("message") if isinstance(body.get("error"), dict) else body.get("error")
            if not msg:
                msg = resp.text[:400]
        except Exception:
            msg = resp.text[:400]
        raise RuntimeError(f"Google Calendar {action} failed ({resp.status_code}): {str(msg)[:400]}")

    def health(self) -> ProviderHealth:
        try:
            token, cal_id, tenant_id = self._resolve_token_and_calendar()
        except (RuntimeError, PermissionError) as e:
            return ProviderHealth(status=CalendarProviderStatus.UNAVAILABLE, provider="Google Calendar", message=str(e)[:400])
        except Exception as e:
            return ProviderHealth(status=CalendarProviderStatus.ERROR, provider="Google Calendar", message=f"Health check error: {str(e)[:200]}")

        # Verify token + calendar access with a lightweight calendarList or calendars/get call
        url = f"{GOOGLE_CALENDAR_BASE}/calendars/{quote(cal_id, safe='')}"
        try:
            resp = requests.get(url, headers=self._auth_headers(token), timeout=12)
        except Exception as e:
            return ProviderHealth(status=CalendarProviderStatus.ERROR, provider="Google Calendar", message=f"Network error: {str(e)[:200]}")
        if resp.status_code == 200:
            return ProviderHealth(status=CalendarProviderStatus.AVAILABLE, provider="Google Calendar", message="Connected")
        if resp.status_code in (401, 403):
            return ProviderHealth(status=CalendarProviderStatus.UNAVAILABLE, provider="Google Calendar", message=f"Authorization failed ({resp.status_code}). Reconnect.")
        return ProviderHealth(status=CalendarProviderStatus.ERROR, provider="Google Calendar", message=f"Health check failed ({resp.status_code})")

    def get_events(self, query: ProviderEventQuery) -> ProviderEventsResult:
        try:
            token, cal_id, _ = self._resolve_token_and_calendar()
        except (RuntimeError, PermissionError) as e:
            return ProviderEventsResult(success=False, events=[], message=str(e)[:400])
        except Exception as e:
            return ProviderEventsResult(success=False, events=[], message=f"Failed to resolve Google connection: {str(e)[:300]}")

        # Google events.list
        params: dict[str, Any] = {
            "calendarId": cal_id,
            "timeMin": query.start.isoformat().replace("+00:00", "Z") if query.start.tzinfo else query.start.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z"),
            "timeMax": query.end.isoformat().replace("+00:00", "Z") if query.end.tzinfo else query.end.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z"),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 250,
            "showDeleted": "false",
        }
        # Ensure aware
        if query.start.tzinfo is None:
            params["timeMin"] = query.start.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
        if query.end.tzinfo is None:
            params["timeMax"] = query.end.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")

        url = f"{GOOGLE_CALENDAR_BASE}/calendars/{quote(cal_id, safe='')}/events"
        try:
            resp = requests.get(url, headers=self._auth_headers(token), params=params, timeout=20)
        except Exception as e:
            return ProviderEventsResult(success=False, events=[], message=f"Google get_events network error: {str(e)[:300]}")

        if resp.status_code == 401:
            # Try one token refresh retry if not already refreshed
            try:
                from heshly_core.services.google.google_calendar_token_service import get_valid_access_token
                # Force refresh by expiring current
                tenant_id = self._tenant_context.require()
                repo = self._get_repository()
                # Attempt refresh: get_valid_access_token will handle refresh if needed; retry once
                # We signal expiry by fetching again (token service checks skew)
                # As fallback, directly refresh if we have refresh_token
                # Simple: retry once after invalidating access_token expiry
                # For ephemeral path token already refreshed; for persisted, re-resolve
                if self._connection is None:
                    # Persisted: short-circuit — ask token service fresh
                    try:
                        fresh_token, _ = get_valid_access_token(tenant_id, repository=repo)
                        resp2 = requests.get(url, headers=self._auth_headers(fresh_token), params=params, timeout=20)
                        if resp2.status_code == 200:
                            resp = resp2
                        elif resp2.status_code == 401:
                            return ProviderEventsResult(success=False, events=[], message="Google authorization expired or revoked (401). Please reconnect.")
                        elif resp2.status_code != 200:
                            self._handle_api_error(resp2, "get_events")
                    except PermissionError as pe:
                        return ProviderEventsResult(success=False, events=[], message=str(pe)[:400])
            except Exception:
                pass
            if resp.status_code == 401:
                return ProviderEventsResult(success=False, events=[], message="Google authorization expired or revoked (401). Please reconnect.")

        if resp.status_code != 200:
            try:
                self._handle_api_error(resp, "get_events")
            except (RuntimeError, PermissionError) as e:
                return ProviderEventsResult(success=False, events=[], message=str(e)[:400])

        try:
            data = resp.json()
        except Exception as e:
            return ProviderEventsResult(success=False, events=[], message=f"Invalid Google response: {str(e)[:300]}")

        items = data.get("items") or []
        events: list[CalendarEvent] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            if status == "cancelled":
                continue  # exclude cancelled
            summary = item.get("summary") or "(No title)"
            cal_event_id = item.get("id") or ""
            start_obj = item.get("start")
            end_obj = item.get("end")
            start_dt = _parse_google_datetime(start_obj, "UTC")
            end_dt = _parse_google_datetime(end_obj, "UTC")
            if start_dt is None:
                continue
            if end_dt is None:
                # All-day end defaults to next day; if missing treat as start+24h
                try:
                    from datetime import timedelta
                    end_dt = start_dt + timedelta(days=1)
                except Exception:
                    end_dt = start_dt
            description = item.get("description") or ""
            # Try to extract customer fields from description if present (best-effort)
            display_tz = item.get("start", {}).get("timeZone") if isinstance(item.get("start"), dict) else None
            events.append(
                CalendarEvent(
                    event_id=cal_event_id,
                    title=summary,
                    start=start_dt,
                    end=end_dt,
                    notes=description or None,
                    status=_event_status_blocking(status),
                )
            )

        return ProviderEventsResult(success=True, events=events, message=f"{len(events)} event(s) found.")

    def create_event(self, event: CalendarEvent) -> ProviderAppointmentResult:
        try:
            token, cal_id, _ = self._resolve_token_and_calendar()
        except (RuntimeError, PermissionError) as e:
            return ProviderAppointmentResult(success=False, event_id=None, message=str(e)[:400])

        # Build Google event body
        body: dict[str, Any] = {
            "summary": event.title,
            "description": event.notes or "",
        }
        # Store customer info in description (Google has no dedicated fields); keep structured prefix
        extras = []
        if event.customer_name:
            extras.append(f"Customer: {event.customer_name}")
        if event.customer_phone:
            extras.append(f"Phone: {event.customer_phone}")
        if extras:
            body["description"] = (body["description"] + "\n" if body["description"] else "") + "\n".join(extras)

        # Use timezone-aware RFC3339
        def _fmt(dt: datetime) -> str:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.isoformat().replace("+00:00", "Z") if dt.tzinfo == UTC else dt.isoformat()

        body["start"] = {"dateTime": _fmt(event.start)}
        body["end"] = {"dateTime": _fmt(event.end)}

        url = f"{GOOGLE_CALENDAR_BASE}/calendars/{quote(cal_id, safe='')}/events"
        try:
            resp = requests.post(url, headers=self._auth_headers(token), json=body, timeout=20)
        except Exception as e:
            return ProviderAppointmentResult(success=False, event_id=None, message=f"Google create_event network error: {str(e)[:300]}")

        if resp.status_code not in (200, 201):
            try:
                self._handle_api_error(resp, "create_event")
            except (RuntimeError, PermissionError) as e:
                return ProviderAppointmentResult(success=False, event_id=None, message=str(e)[:400])

        try:
            data = resp.json()
        except Exception:
            return ProviderAppointmentResult(success=False, event_id=None, message="Invalid Google create response")
        gid = data.get("id")
        return ProviderAppointmentResult(success=True, event_id=gid, message=f"Google event {gid} created.")

    def update_event(self, event: CalendarEvent) -> ProviderAppointmentResult:
        if not event.event_id:
            return ProviderAppointmentResult(success=False, event_id=None, message="event_id is required for update")
        try:
            token, cal_id, _ = self._resolve_token_and_calendar()
        except (RuntimeError, PermissionError) as e:
            return ProviderAppointmentResult(success=False, event_id=event.event_id, message=str(e)[:400])

        body: dict[str, Any] = {
            "summary": event.title,
            "description": event.notes or "",
        }
        if event.customer_name or event.customer_phone:
            extras = []
            if event.customer_name:
                extras.append(f"Customer: {event.customer_name}")
            if event.customer_phone:
                extras.append(f"Phone: {event.customer_phone}")
            body["description"] = (body["description"] + "\n" if body["description"] else "") + "\n".join(extras)

        def _fmt(dt: datetime) -> str:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.isoformat().replace("+00:00", "Z") if dt.tzinfo == UTC else dt.isoformat()

        body["start"] = {"dateTime": _fmt(event.start)}
        body["end"] = {"dateTime": _fmt(event.end)}

        url = f"{GOOGLE_CALENDAR_BASE}/calendars/{quote(cal_id, safe='')}/events/{quote(event.event_id, safe='')}"
        try:
            resp = requests.patch(url, headers=self._auth_headers(token), json=body, timeout=20)
        except Exception as e:
            return ProviderAppointmentResult(success=False, event_id=event.event_id, message=f"Google update_event network error: {str(e)[:300]}")

        # Fallback: some Google API versions use PUT
        if resp.status_code == 405:
            try:
                resp = requests.put(url, headers=self._auth_headers(token), json=body, timeout=20)
            except Exception:
                pass

        if resp.status_code not in (200, 201):
            try:
                self._handle_api_error(resp, "update_event")
            except (RuntimeError, PermissionError) as e:
                return ProviderAppointmentResult(success=False, event_id=event.event_id, message=str(e)[:400])

        try:
            data = resp.json()
        except Exception:
            data = {}
        gid = data.get("id") or event.event_id
        return ProviderAppointmentResult(success=True, event_id=gid, message=f"Google event {gid} updated.")

    def delete_event(self, event_id: str) -> ProviderAppointmentResult:
        if not event_id or not str(event_id).strip():
            return ProviderAppointmentResult(success=False, event_id=event_id, message="event_id is required for delete")
        try:
            token, cal_id, _ = self._resolve_token_and_calendar()
        except (RuntimeError, PermissionError) as e:
            return ProviderAppointmentResult(success=False, event_id=event_id, message=str(e)[:400])

        url = f"{GOOGLE_CALENDAR_BASE}/calendars/{quote(cal_id, safe='')}/events/{quote(str(event_id).strip(), safe='')}"
        try:
            resp = requests.delete(url, headers=self._auth_headers(token), timeout=15)
        except Exception as e:
            return ProviderAppointmentResult(success=False, event_id=event_id, message=f"Google delete_event network error: {str(e)[:300]}")

        if resp.status_code in (200, 204):
            return ProviderAppointmentResult(success=True, event_id=event_id, message=f"Google event {event_id} deleted.")
        if resp.status_code == 410:
            return ProviderAppointmentResult(success=True, event_id=event_id, message=f"Google event {event_id} already deleted.")
        try:
            self._handle_api_error(resp, "delete_event")
        except (RuntimeError, PermissionError) as e:
            return ProviderAppointmentResult(success=False, event_id=event_id, message=str(e)[:400])
        return ProviderAppointmentResult(success=False, event_id=event_id, message=f"Google delete failed ({resp.status_code})")
