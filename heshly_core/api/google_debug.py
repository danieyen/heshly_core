from __future__ import annotations

import frappe
from datetime import datetime, UTC, timedelta

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_provider import ProviderEventQuery
from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider


def _require_tenant() -> str:
    return TenantContext().require()


@frappe.whitelist(allow_guest=False)
def status():
    """Delegates to google_oauth.status but exposed under google_debug for tooling."""
    from heshly_core.api.google_oauth import status as oauth_status

    return oauth_status()


@frappe.whitelist(allow_guest=False)
def list_calendars():
    from heshly_core.api.google_oauth import list_calendars as oauth_list

    return oauth_list()


@frappe.whitelist(allow_guest=False)
def health():
    tenant_id = _require_tenant()
    provider = GoogleCalendarProvider()
    h = provider.health()
    # Never leak tokens; message is already sanitized
    return {
        "success": True,
        "tenant_id": tenant_id,
        "provider": h.provider,
        "status": h.status.value if hasattr(h.status, "value") else str(h.status),
        "message": h.message,
    }


@frappe.whitelist(allow_guest=False)
def test_get_events(timeMin: str | None = None, timeMax: str | None = None):
    """
    Safe live debug: fetch events for a small window (default: now → +24h).
    Never exposes tokens. Returns count + normalized events (notes truncated).
    """
    tenant_id = _require_tenant()
    provider = GoogleCalendarProvider()
    # Default window: now → +24h
    now = datetime.now(UTC)
    try:
        start = datetime.fromisoformat((timeMin or "").replace("Z", "+00:00")) if timeMin else now
        end = datetime.fromisoformat((timeMax or "").replace("Z", "+00:00")) if timeMax else (now + timedelta(hours=24))
    except Exception:
        frappe.throw("Invalid timeMin/timeMax — expected ISO 8601", frappe.ValidationError)

    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)

    result = provider.get_events(ProviderEventQuery(start=start, end=end))
    # Truncate notes so response stays small and never leaks raw description PII in logs
    safe_events = []
    for e in result.events[:10]:
        safe_events.append(
            {
                "event_id": e.event_id,
                "title": e.title,
                "start": e.start.isoformat() if e.start else None,
                "end": e.end.isoformat() if e.end else None,
                "notes_preview": (e.notes[:120] + "…") if e.notes and len(e.notes) > 120 else (e.notes or None),
                "status": e.status.value if hasattr(e.status, "value") else str(e.status),
            }
        )
    return {
        "success": result.success,
        "tenant_id": tenant_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "count": len(result.events),
        "message": result.message,
        "events": safe_events,
    }


@frappe.whitelist(allow_guest=False)
def test_create_event(title: str | None = None, minutes_from_now: int = 60, duration_minutes: int = 30):
    """
    Safe live debug: create a test event 60 minutes in the future (default) so it never collides with current slots.
    Caller must be authenticated as tenant owner; event is created in that tenant's Google calendar.

    Use sparingly — creates a real Google event. You can pass title override.
    """
    tenant_id = _require_tenant()
    from heshly_core.models.calendar import CalendarEvent

    provider = GoogleCalendarProvider()
    now = datetime.now(UTC)
    try:
        offset = int(minutes_from_now) if minutes_from_now is not None else 60
        dur = int(duration_minutes) if duration_minutes is not None else 30
    except Exception:
        frappe.throw("minutes_from_now / duration_minutes must be integers", frappe.ValidationError)

    start = now + timedelta(minutes=offset)
    end = start + timedelta(minutes=dur)
    ev = CalendarEvent(
        event_id="",
        title=(title or f"Heshly Debug Event {start.strftime('%Y-%m-%d %H:%M UTC')}"),
        start=start,
        end=end,
        notes=f"Heshly debug test event — tenant={tenant_id} — safe to delete.",
    )

    result = provider.create_event(ev)
    return {
        "success": result.success,
        "tenant_id": tenant_id,
        "event_id": result.event_id,
        "message": result.message,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
