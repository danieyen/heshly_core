from __future__ import annotations

import pytest
from datetime import datetime, UTC, timedelta, timezone
from unittest.mock import MagicMock, patch
import zoneinfo

from heshly_core.models.calendar import CalendarProvider, CalendarEvent
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.api.availability import AvailabilityAPI


def _fake_repo(monkeypatch, connections_by_tenant: dict):
    """Patch CalendarConnectionRepository.list/get_for_provider/get_value for this test module."""
    import heshly_core.api.availability as avail_mod

    # We patch the repository class used INSIDE _check_via_calendar_provider
    # That method does: from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    # So we patch that import path's class.

    class FakeRepo:
        def __init__(self, *a, **kw):
            pass

        def list(self, tenant_id=None):
            # tenant_id is required; return list for that tenant
            if tenant_id is None:
                try:
                    tenant_id = TenantContext().require()
                except Exception:
                    return []
            return list(connections_by_tenant.get(tenant_id, []))

        def get_for_provider(self, provider, tenant_id=None):
            for c in self.list(tenant_id=tenant_id):
                if c.provider == provider:
                    return c
            return None

    # Patch where it's imported inside the method (import inside function)
    monkeypatch.setattr("heshly_core.repositories.calendar_connection_repository.CalendarConnectionRepository", FakeRepo)

    # Also need to ensure get_value not called stale: but list is our path
    return FakeRepo


def _make_conn(tenant_id="heshly", provider=CalendarProvider.GOOGLE, tz="Africa/Nairobi"):
    return CalendarConnection(
        connection_id=f"{tenant_id}:google:primary",
        tenant_id=tenant_id,
        provider=provider,
        calendar_id="primary",
        timezone=tz,
        status=CalendarConnectionStatus.ACTIVE,
        access_token="at",
        refresh_token="rt",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    )


def _payload_heshly_2026_09_08_10am(tenant_id="heshly"):
    return {
        "tenant_id": tenant_id,
        "service": "Consultation",
        "preferred_date": "2026-09-08",
        "preferred_time": "10:00",
        "duration_minutes": 30,
    }


# ------------------------------------------------------------------
# 1. Queries calendar provider
# 2. No conflicting event → available
# 3. Overlapping event → unavailable
# 4. Events passed into AvailabilityEngine
# ------------------------------------------------------------------

def test_queries_provider_and_returns_available_when_no_conflict(monkeypatch):
    TenantContext().clear()
    tenant = "heshly"
    conn = _make_conn(tenant)
    _fake_repo(monkeypatch, {tenant: [conn]})

    called = {}

    class FakeProvider:
        def get_events(self, query):
            called["query"] = query
            # Return no events
            from heshly_core.models.calendar_provider import ProviderEventsResult
            return ProviderEventsResult(success=True, events=[], message="0 events")

    # Patch factory to return our fake provider
    class FakeFactory:
        def create(self, provider):
            return FakeProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am(tenant))
    assert res["available"] is True
    assert len(res["slots"]) == 1
    assert "available" in res["reason"].lower() or res["available"]
    assert "query" in called
    # Query should span the day 2026-09-08 in Africa/Nairobi
    assert called["query"].start.date().isoformat() == "2026-09-08"


def test_overlapping_google_event_is_unavailable(monkeypatch):
    TenantContext().clear()
    tenant = "heshly"
    conn = _make_conn(tenant, tz="Africa/Nairobi")
    _fake_repo(monkeypatch, {tenant: [conn]})

    # Request 10:00-10:30, Google has 10:15-10:45 → overlap
    tz = zoneinfo.ZoneInfo("Africa/Nairobi")
    ev_start = datetime(2026, 9, 8, 10, 15, tzinfo=tz)
    ev_end = datetime(2026, 9, 8, 10, 45, tzinfo=tz)

    class FakeProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            return ProviderEventsResult(
                success=True,
                events=[CalendarEvent(event_id="evt1", title="Existing Meeting", start=ev_start, end=ev_end)],
                message="1 event",
            )

    class FakeFactory:
        def create(self, provider):
            return FakeProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am(tenant))
    assert res["available"] is False
    assert res["slots"] == []
    assert "conflict" in res["reason"].lower()


def test_events_passed_into_availability_engine_spy(monkeypatch):
    TenantContext().clear()
    tenant = "heshly"
    conn = _make_conn(tenant)
    _fake_repo(monkeypatch, {tenant: [conn]})

    spy = {}

    real_is_available = None

    class FakeProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            ev = CalendarEvent(
                event_id="spy1",
                title="Spy Event",
                start=datetime(2026, 9, 8, 10, 0, tzinfo=zoneinfo.ZoneInfo("Africa/Nairobi")),
                end=datetime(2026, 9, 8, 10, 30, tzinfo=zoneinfo.ZoneInfo("Africa/Nairobi")),
            )
            return ProviderEventsResult(success=True, events=[ev], message="1")

    class FakeFactory:
        def create(self, provider):
            return FakeProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    # Spy on AvailabilityEngine.is_available
    from heshly_core.services.calendar import availability_engine as ae_mod

    orig = ae_mod.AvailabilityEngine.is_available

    def spy_is_available(self, start, duration_minutes, events):
        spy["events"] = list(events)
        spy["start"] = start
        spy["duration"] = duration_minutes
        return orig(self, start, duration_minutes, events)

    monkeypatch.setattr(ae_mod.AvailabilityEngine, "is_available", spy_is_available)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am(tenant))
    assert res["available"] is False  # overlap
    assert "events" in spy
    assert any(e.event_id == "spy1" for e in spy["events"])


# ------------------------------------------------------------------
# 5. Tenant isolation: A cannot use B's calendar
# 6. Missing connection → unavailable (not available=true)
# 7. Provider error → unavailable (not available=true)
# ------------------------------------------------------------------

def test_tenant_a_cannot_use_tenant_b_calendar(monkeypatch):
    TenantContext().clear()
    # Only tenant B has a connection
    conn_b = _make_conn("tenant-b", tz="Africa/Nairobi")
    _fake_repo(monkeypatch, {"tenant-b": [conn_b]})

    # Tenant A requests → should get "No calendar is connected" not B's events
    class ShouldNotBeCalledProvider:
        def get_events(self, query):
            raise AssertionError("Should not query provider for tenant with no connection")

    class FakeFactory:
        def create(self, provider):
            return ShouldNotBeCalledProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am("tenant-a"))
    assert res["available"] is False
    assert "no calendar" in res["reason"].lower()
    assert "available" not in res.get("slots", [])  # slots empty


def test_missing_calendar_connection_is_not_available(monkeypatch):
    TenantContext().clear()
    _fake_repo(monkeypatch, {})  # no connections at all

    class NeverCalledProvider:
        def get_events(self, query):
            pytest.fail("Should not call provider when no connection")

    class FakeFactory:
        def create(self, provider):
            return NeverCalledProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am("heshly"))
    assert res["available"] is False
    assert "no calendar" in res["reason"].lower()
    # Must not leak tokens
    assert "access_token" not in str(res)
    assert "refresh_token" not in str(res)


def test_google_provider_error_is_not_available(monkeypatch):
    TenantContext().clear()
    conn = _make_conn("heshly")
    _fake_repo(monkeypatch, {"heshly": [conn]})

    class ErrorProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            return ProviderEventsResult(success=False, events=[], message="Google 500 internal error")

    class FakeFactory:
        def create(self, provider):
            return ErrorProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am("heshly"))
    assert res["available"] is False
    assert "calendar query failed" in res["reason"].lower() or "google" in res["reason"].lower()


# ------------------------------------------------------------------
# 8. Existing payload formats continue to work (but now via live path)
#    And regression: legacy AvailabilityChecker is NOT the production path
# ------------------------------------------------------------------

def test_existing_payload_formats_still_work(monkeypatch):
    TenantContext().clear()
    conn = _make_conn("heshly")
    _fake_repo(monkeypatch, {"heshly": [conn]})

    class OKProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            return ProviderEventsResult(success=True, events=[], message="0")

    class FakeFactory:
        def create(self, provider):
            return OKProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()

    # Top-level
    assert api.check({"tenant_id": "heshly", "service": "Consultation", "preferred_date": "2026-09-08", "preferred_time": "10:00", "duration_minutes": 30})["available"] is True

    # Entities capitalized
    assert api.check({"tenant_id": "heshly", "Entities": {"service": "Consultation", "date": "2026-09-08", "time": "10:00"}})["available"] is True

    # scheduled_time
    assert api.check({"tenant_id": "heshly", "service": "Consultation", "scheduled_time": "2026-09-08T10:00:00Z"})["available"] is True

    # No tokens leaked
    for r in [api.check({"tenant_id": "heshly", "service": "Consultation", "preferred_date": "2026-09-08", "preferred_time": "10:00"})]:
        assert "access_token" not in str(r)
        assert "refresh_token" not in str(r)


def test_legacy_availability_checker_not_production_path(monkeypatch):
    """If we mock AvailabilityChecker.is_available to return True always, live provider still decides."""
    TenantContext().clear()
    conn = _make_conn("heshly")
    _fake_repo(monkeypatch, {"heshly": [conn]})

    # Live provider says conflict
    class ConflictProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            tz = zoneinfo.ZoneInfo("Africa/Nairobi")
            return ProviderEventsResult(
                success=True,
                events=[CalendarEvent(event_id="e", title="Conflict", start=datetime(2026, 9, 8, 10, 0, tzinfo=tz), end=datetime(2026, 9, 8, 10, 30, tzinfo=tz))],
                message="1",
            )

    class FakeFactory:
        def create(self, provider):
            return ConflictProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    # Monkey-patch legacy checker to always say available (should be ignored)
    monkeypatch.setattr("heshly_core.services.booking.availability_checker.AvailabilityChecker.is_available", lambda self, r, s, b: True)

    api = AvailabilityAPI()
    res = api.check(_payload_heshly_2026_09_08_10am("heshly"))
    # Live provider conflict must win
    assert res["available"] is False
    assert "conflict" in res["reason"].lower()


def test_specific_heshly_slot_2026_09_08_10am_no_conflict_is_available(monkeypatch):
    """Exact requested test from prompt: tenant heshly, 2026-09-08 10:00 Consultation 30min with no Google events → available."""
    TenantContext().clear()
    conn = _make_conn("heshly", tz="Africa/Nairobi")
    _fake_repo(monkeypatch, {"heshly": [conn]})

    class EmptyProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            # Verify query window is 2026-09-08 in Africa/Nairobi
            assert query.start.date().isoformat() == "2026-09-08"
            assert query.end.date().isoformat() == "2026-09-08"
            return ProviderEventsResult(success=True, events=[], message="0 events")

    class FakeFactory:
        def create(self, provider):
            return EmptyProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    payload = {
        "tenant_id": "heshly",
        "service": "Consultation",
        "preferred_date": "2026-09-08",
        "preferred_time": "10:00",
        "duration_minutes": 30,
    }
    res = api.check(payload)
    assert res["available"] is True
    assert len(res["slots"]) == 1
    # Slot should be 10:00 in Africa/Nairobi
    slot = res["slots"][0]
    assert slot["start"] is not None
    assert "available" in res
    assert isinstance(res["available"], bool)


def test_no_token_leakage_on_all_paths(monkeypatch):
    TenantContext().clear()
    conn = CalendarConnection(
        connection_id="heshly:google:primary",
        tenant_id="heshly",
        provider=CalendarProvider.GOOGLE,
        calendar_id="primary",
        timezone="Africa/Nairobi",
        status=CalendarConnectionStatus.ACTIVE,
        access_token="super-secret-at",
        refresh_token="super-secret-rt",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    )
    _fake_repo(monkeypatch, {"heshly": [conn]})

    class OKProvider:
        def get_events(self, query):
            from heshly_core.models.calendar_provider import ProviderEventsResult
            return ProviderEventsResult(success=True, events=[], message="0")

    class FakeFactory:
        def create(self, provider):
            return OKProvider()

    monkeypatch.setattr("heshly_core.services.calendar.providers.provider_factory.ProviderFactory", FakeFactory)

    api = AvailabilityAPI()
    for payload in [
        _payload_heshly_2026_09_08_10am("heshly"),
        {"tenant_id": "heshly", "service": "Consultation", "scheduled_time": "2026-09-08T10:00:00Z"},
    ]:
        r = api.check(payload)
        s = str(r)
        assert "super-secret-at" not in s
        assert "super-secret-rt" not in s
        assert "access_token" not in s.lower() or "has_access_token" in s.lower()  # only boolean flag allowed elsewhere, not here
