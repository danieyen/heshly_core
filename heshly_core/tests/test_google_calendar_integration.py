from __future__ import annotations

import pytest
import json
from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

from heshly_core.models.calendar import CalendarProvider, CalendarEvent
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.models.calendar_provider import ProviderConnection, CalendarConfiguration, ProviderEventQuery
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.google.google_oauth_service import GoogleOAuthService, GoogleOAuthStateStore
from heshly_core.services.google.google_config import GoogleConfig


# ---- Helpers: fake frappe for repository ----

def _fake_frappe_for_repo(monkeypatch):
    import heshly_core.repositories.calendar_connection_repository as mod

    # Reuse same pattern as persistence test
    class FakeDoc:
        def __init__(self, doctype=None, name=None, data=None):
            self.doctype = doctype
            self.name = name or (data.get("name") if data else None)
            self._data = data or {}
        def __getattr__(self, k):
            if k in self._data:
                return self._data[k]
            raise AttributeError(k)
        def __setattr__(self, k, v):
            if k in ("doctype", "name", "_data"):
                object.__setattr__(self, k, v)
            else:
                self._data[k] = v
        def get_password(self, field):
            return self._data.get(field)
        def save(self, ignore_permissions=False):
            self._data["name"] = self._data.get("name") or self._data.get("connection_id")
            store[self._data["name"]] = dict(self._data)
            store[self._data["name"]]["doctype"] = self.doctype
    store: dict[str, dict] = {}
    class FakeDB:
        def get_value(self, doctype, filters, fieldname="name"):
            for key, doc in list(store.items()):
                if doc.get("doctype") != doctype:
                    continue
                match = True
                for fk, fv in (filters or {}).items():
                    if doc.get(fk) != fv:
                        match = False; break
                if match:
                    return doc.get(fieldname) or doc.get("name")
            return None
        def exists(self, doctype, filters):
            return bool(self.get_value(doctype, filters, "name"))
        def get_all(self, doctype, filters=None, pluck=None, **kwargs):
            out=[]
            for doc in store.values():
                if doc.get("doctype") != doctype:
                    continue
                match=True
                for fk,fv in (filters or {}).items():
                    if doc.get(fk)!=fv:
                        match=False;break
                if match:
                    out.append(doc.get(pluck) if pluck else doc)
            return out
        def commit(self): pass
        def escape(self,v): return f"'{v}'"
    fake_frappe = type("F", (), {})()
    fake_frappe.db = FakeDB()
    def fake_new_doc(doctype): return FakeDoc(doctype=doctype, data={"doctype": doctype})
    def fake_get_doc(doctype, name):
        doc = store.get(name)
        if not doc: raise Exception(f"Not found {doctype} {name}")
        return FakeDoc(doctype=doctype, name=name, data=dict(doc))
    def fake_delete_doc(doctype, name, ignore_permissions=True):
        if name in store: del store[name]
    def fake_get_value(doctype, filters, fieldname="name"): return fake_frappe.db.get_value(doctype, filters, fieldname)
    def fake_throw(msg, exc=None): raise Exception(msg)
    def fake_get_all(doctype, filters=None, pluck=None, **kwargs): return fake_frappe.db.get_all(doctype, filters=filters, pluck=pluck)
    fake_frappe.new_doc = fake_new_doc
    fake_frappe.get_doc = fake_get_doc
    fake_frappe.delete_doc = fake_delete_doc
    fake_frappe.get_value = fake_get_value
    fake_frappe.throw = fake_throw
    fake_frappe.get_all = fake_get_all
    fake_frappe.get_site_config = lambda: {}
    fake_frappe.conf = {}
    # frappe.cache stub for state store (in-memory already, but provide minimal)
    class FakeCache:
        def __init__(self): self._d={}
        def set_value(self,k,v,expires_in_sec=None): self._d[k]=v
        def get_value(self,k): return self._d.get(k)
        def delete_value(self,k): self._d.pop(k,None)
        def delete(self,k): self._d.pop(k,None)
    fake_frappe.cache = FakeCache  # call returns object? state store does frappe.cache() call
    orig_cache = fake_frappe.cache
    fake_frappe.cache = lambda: FakeCache()  # but we want singleton: use closure
    # Use singleton cache instance
    cache_inst = FakeCache()
    fake_frappe.cache = lambda: cache_inst
    monkeypatch.setattr(mod, "frappe", fake_frappe, raising=False)
    # also patch heshly_calendar_connection doctype module frappe
    try:
        import heshly_core.heshly_core.doctype.heshly_calendar_connection.heshly_calendar_connection as dtype_mod
        dtype_mod.frappe = fake_frappe
    except Exception:
        pass
    # patch google token service's repo import as well
    return fake_frappe, store


def _get_google_config():
    return GoogleConfig(client_id="test-client-id", client_secret="test-secret", redirect_uri="https://erp.heshly.com/api/method/heshly_core.api.google_oauth.callback", scopes=["https://www.googleapis.com/auth/calendar","https://www.googleapis.com/auth/calendar.events"])


# -- OAuth state isolation --

def test_oauth_state_tenant_isolation(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    # Need frappe module patch for oauth service's cache & secret
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    svc = GoogleOAuthService(config=_get_google_config())
    url_a, state_a = svc.build_authorization_url("tenant-a")
    url_b, state_b = svc.build_authorization_url("tenant-b")
    assert "tenant-a" not in url_a  # state encodes tenant internally but not leaked as plain query? URL contains state opaque
    # Valid consume
    t_a = svc.verify_state(state_a)
    assert t_a == "tenant-a"
    # Replay must fail
    with pytest.raises(PermissionError):
        svc.verify_state(state_a)
    # Cross-tenant: state_b valid for tenant-b only
    t_b = svc.verify_state(state_b)
    assert t_b == "tenant-b"
    # Manipulated state
    with pytest.raises(PermissionError):
        svc.verify_state(state_b + "x")
    # Missing state
    with pytest.raises((ValueError, PermissionError)):
        svc.verify_state("")


def test_authorization_code_exchange_and_token_refresh_mock(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    svc = GoogleOAuthService(config=_get_google_config())

    # Mock requests.post for token exchange
    fake_token_resp = MagicMock()
    fake_token_resp.status_code = 200
    fake_token_resp.json.return_value = {"access_token":"at123","refresh_token":"rt123","expires_in":3600,"scope":"https://www.googleapis.com/auth/calendar","token_type":"Bearer"}

    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=fake_token_resp) as mock_post:
        result = svc.exchange_code("authcode123")
        assert result["access_token"] == "at123"
        assert result["refresh_token"] == "rt123"
        assert result["expires_at"] is not None
        # Must be naive UTC for MariaDB Datetime field (no +00:00 suffix)
        assert result["expires_at"].tzinfo is None, "expires_at must be naive UTC for DB"
        # Compare as naive UTC
        assert result["expires_at"] > datetime.now(UTC).replace(tzinfo=None)
        # Ensure data posted does not log token (just verify call shape)
        args, kwargs = mock_post.call_args
        assert "access_token" not in str(kwargs.get("data", {}))  # code only, not token echo

    # Refresh
    fake_refresh_resp = MagicMock()
    fake_refresh_resp.status_code = 200
    fake_refresh_resp.json.return_value = {"access_token":"at_new","expires_in":3600}
    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=fake_refresh_resp):
        refreshed = svc.refresh_access_token("rt123")
        assert refreshed["access_token"] == "at_new"
        assert refreshed["expires_at"].tzinfo is None, "refresh expires_at must be naive UTC"

    # Expired token refresh failure maps to revoked message (tested via token service)
    fake_fail = MagicMock()
    fake_fail.status_code = 400
    fake_fail.json.return_value = {"error":"invalid_grant","error_description":"Token has been expired or revoked."}
    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=fake_fail):
        with pytest.raises(RuntimeError, match="invalid_grant|revoked|expired"):
            svc.refresh_access_token("bad_rt")


def test_token_lifecycle_expired_auto_refresh_persists(monkeypatch):
    fake_frappe, store = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    # Also patch token service's frappe reference indirectly via repo already patched
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    from heshly_core.services.google.google_calendar_token_service import get_valid_access_token
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-a")
    # Save expired connection
    expired_conn = CalendarConnection(
        connection_id="tenant-a:google:primary",
        tenant_id="tenant-a",
        provider=CalendarProvider.GOOGLE,
        calendar_id="primary",
        timezone="Africa/Nairobi",
        access_token="old_at",
        refresh_token="rt123",
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        status=CalendarConnectionStatus.ACTIVE,
    )
    repo.save(expired_conn)
    # Mock refresh
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"access_token":"fresh_at","expires_in":3600}
    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=fake_resp):
        # Also ensure google config loads without frappe.conf error
        monkeypatch.setattr("heshly_core.services.google.google_config._get_conf_value", lambda k, ek=None: {"google_client_id":"cid","google_client_secret":"sec","google_redirect_uri":"https://erp.heshly.com/api/method/heshly_core.api.google_oauth.callback"}.get(k))
        with patch("heshly_core.services.google.google_oauth_service.load_google_config", return_value=_get_google_config()):
            token, conn = get_valid_access_token("tenant-a", repository=repo)
            assert token == "fresh_at"
            assert conn.access_token == "fresh_at"
            # Persisted expires_at must be naive UTC (MariaDB-safe)
            assert conn.expires_at is None or conn.expires_at.tzinfo is None
            # Verify persisted and naive
            reloaded = repo.get("tenant-a:google:primary", tenant_id="tenant-a")
            assert reloaded.access_token == "fresh_at"
            assert reloaded.expires_at is None or reloaded.expires_at.tzinfo is None


def test_calendar_discovery_safe_no_tokens(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    svc = GoogleOAuthService(config=_get_google_config())
    fake_cal_list = MagicMock()
    fake_cal_list.status_code = 200
    fake_cal_list.json.return_value = {
        "items":[
            {"id":"primary","summary":"My Primary","timeZone":"Africa/Nairobi","primary":True,"accessRole":"owner","backgroundColor":"#039BE5","selected":True},
            {"id":"work@example.com","summary":"Work","timeZone":"America/New_York","accessRole":"reader"},
        ]
    }
    with patch("heshly_core.services.google.google_oauth_service.requests.get", return_value=fake_cal_list):
        cals = svc.list_calendars("fake_at")
        assert len(cals) == 2
        assert cals[0]["calendar_id"] == "primary"
        assert cals[0]["primary"] is True
        # Ensure no token in returned data
        assert "fake_at" not in json.dumps(cals)
        assert "access_token" not in json.dumps(cals)


def test_google_provider_get_events_normalization(monkeypatch):
    fake_frappe, store = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
    # Prepare tenant-a connection
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-a")
    repo.save(CalendarConnection(connection_id="tenant-a:google:primary", tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="Africa/Nairobi", access_token="valid_at", refresh_token="rt", expires_at=datetime.now(UTC)+timedelta(hours=1)))
    provider = GoogleCalendarProvider(repository=repo)
    # Mock Google events.list: one timed, one all-day, one cancelled
    google_items = {
        "items":[
            {"id":"evt1","summary":"Meeting A","status":"confirmed","start":{"dateTime":"2026-09-08T10:00:00+03:00"},"end":{"dateTime":"2026-09-08T11:00:00+03:00"},"description":"Notes A"},
            {"id":"evt2","summary":"All Day Event","status":"confirmed","start":{"date":"2026-09-09"},"end":{"date":"2026-09-10"}},
            {"id":"evt3","summary":"Cancelled Event","status":"cancelled","start":{"dateTime":"2026-09-08T12:00:00+03:00"},"end":{"dateTime":"2026-09-08T13:00:00+03:00"}},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = google_items
    with patch("heshly_core.services.calendar.providers.google_calendar_provider.requests.get", return_value=mock_resp):
        result = provider.get_events(ProviderEventQuery(start=datetime(2026,9,8,0,0,tzinfo=UTC), end=datetime(2026,9,10,0,0,tzinfo=UTC)))
        assert result.success is True
        assert len(result.events) == 2  # cancelled excluded
        titles = {e.title for e in result.events}
        assert "Meeting A" in titles
        assert "All Day Event" in titles
        # Timed event should be UTC-aware
        mtg = next(e for e in result.events if e.title == "Meeting A")
        assert mtg.start.tzinfo is not None
        # Ensure cancelled not present
        assert "Cancelled Event" not in titles


def test_google_provider_create_update_delete(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-a")
    repo.save(CalendarConnection(connection_id="tenant-a:google:primary", tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="Africa/Nairobi", access_token="at", refresh_token="rt", expires_at=datetime.now(UTC)+timedelta(hours=1)))
    provider = GoogleCalendarProvider(repository=repo)

    # create
    mock_create = MagicMock()
    mock_create.status_code = 200
    mock_create.json.return_value = {"id":"google-evt-123"}
    with patch("heshly_core.services.calendar.providers.google_calendar_provider.requests.post", return_value=mock_create) as mock_post:
        res = provider.create_event(CalendarEvent(event_id="tmp", title="Test Booking", start=datetime(2026,9,10,9,0,tzinfo=UTC), end=datetime(2026,9,10,10,0,tzinfo=UTC), customer_name="Alice", customer_phone="+254700000000", notes="VIP"))
        assert res.success is True
        assert res.event_id == "google-evt-123"
        # Body should contain summary and dateTime, not leaked token
        body = mock_post.call_args.kwargs.get("json", {})
        assert body.get("summary") == "Test Booking"
        assert "secret" not in json.dumps(body) and "refresh" not in json.dumps(body).lower()

    # update (patch)
    mock_update = MagicMock()
    mock_update.status_code = 200
    mock_update.json.return_value = {"id":"google-evt-123"}
    with patch("heshly_core.services.calendar.providers.google_calendar_provider.requests.patch", return_value=mock_update):
        res = provider.update_event(CalendarEvent(event_id="google-evt-123", title="Updated", start=datetime(2026,9,10,9,0,tzinfo=UTC), end=datetime(2026,9,10,10,0,tzinfo=UTC)))
        assert res.success is True
        assert res.event_id == "google-evt-123"

    # delete
    mock_del = MagicMock()
    mock_del.status_code = 204
    with patch("heshly_core.services.calendar.providers.google_calendar_provider.requests.delete", return_value=mock_del):
        res = provider.delete_event("google-evt-123")
        assert res.success is True


def test_health_token_validation_not_just_record(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    # No connection → health UNAVAILABLE
    ctx.set("tenant-x")
    provider = GoogleCalendarProvider(repository=repo)
    h = provider.health()
    # Should be UNAVAILABLE or ERROR, NOT AVAILABLE
    assert h.status.value != "available"

    # With connection but invalid token → 401 → UNAVAILABLE
    ctx.set("tenant-a")
    repo.save(CalendarConnection(connection_id="tenant-a:google:primary", tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="Africa/Nairobi", access_token="bad_at", refresh_token=None, expires_at=None))
    mock_bad = MagicMock()
    mock_bad.status_code = 401
    mock_bad.json.return_value = {"error":{"message":"Invalid Credentials"}}
    with patch("heshly_core.services.calendar.providers.google_calendar_provider.requests.get", return_value=mock_bad):
        h2 = provider.health()
        assert h2.status.value in ("unavailable", "error")
        assert "401" in h2.message or "revoked" in h2.message.lower() or "expired" in h2.message.lower() or "authorization" in h2.message.lower()


def test_tenant_a_cannot_access_tenant_b_connection(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
    repo = CalendarConnectionRepository()
    # Tenant A connection
    ctx = TenantContext()
    ctx.set("tenant-a")
    repo.save(CalendarConnection(connection_id="tenant-a:google:primary", tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="Africa/Nairobi", access_token="at-a", refresh_token="rt-a", expires_at=datetime.now(UTC)+timedelta(hours=1)))
    # Switch to tenant-b, same provider should not leak
    ctx.set("tenant-b")
    # Ensure repo enforces isolation: get should return None for cross-tenant
    assert repo.get("tenant-a:google:primary", tenant_id="tenant-b") is None
    assert repo.get_for_provider(CalendarProvider.GOOGLE, tenant_id="tenant-b") is None
    # Provider for tenant-b has no connection → get_events fails safely
    provider_b = GoogleCalendarProvider(repository=repo)
    res = provider_b.get_events(ProviderEventQuery(start=datetime(2026,9,8,0,0,tzinfo=UTC), end=datetime(2026,9,9,0,0,tzinfo=UTC)))
    assert res.success is False
    assert "No Google Calendar connection" in res.message or "tenant" in res.message.lower()


def test_public_apis_never_serialize_tokens(monkeypatch):
    fake_frappe, _ = _fake_frappe_for_repo(monkeypatch)
    import heshly_core.services.google.google_oauth_service as oauth_mod
    monkeypatch.setattr(oauth_mod, "frappe", fake_frappe, raising=False)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    from heshly_core.services.calendar.calendar_connection_service import CalendarConnectionService
    from heshly_core.api.calendar_connection_api import CalendarConnectionAPI
    from heshly_core.services.calendar.providers.google_calendar_provider import GoogleCalendarProvider
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-a")
    svc = CalendarConnectionService(repository=repo, tenant_context=ctx)
    svc.save(CalendarConnection(connection_id="tenant-a:google:primary", tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="Africa/Nairobi", access_token="secret_at", refresh_token="secret_rt", expires_at=datetime.now(UTC)+timedelta(hours=1), business_name="My Biz"))
    api = CalendarConnectionAPI(tenant_context=ctx, service=svc)
    lst = api.list({})
    assert "secret_at" not in json.dumps(lst)
    assert "secret_rt" not in json.dumps(lst)
    assert lst["connections"][0]["has_access_token"] is True  # boolean flag only
    # Provider results also must not leak
    provider = GoogleCalendarProvider(repository=repo)
    # Health message must not contain token
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"timeZone":"Africa/Nairobi","id":"primary"}
    with patch("heshly_core.services.calendar.providers.google_calendar_provider.requests.get", return_value=mock_resp):
        h = provider.health()
        assert "secret_at" not in h.message
        assert "secret_rt" not in h.message
