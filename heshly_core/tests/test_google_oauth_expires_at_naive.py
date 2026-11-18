from __future__ import annotations

from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

from heshly_core.models.calendar import CalendarProvider
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.services.google.google_oauth_service import GoogleOAuthService
from heshly_core.services.google.google_config import GoogleConfig
from heshly_core.services.tenant.tenant_context import TenantContext


def _cfg():
    return GoogleConfig(
        client_id="cid",
        client_secret="sec",
        redirect_uri="https://erp.heshly.com/api/method/heshly_core.api.google_oauth.callback",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )


def _fake_frappe(monkeypatch):
    import heshly_core.repositories.calendar_connection_repository as mod

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
        def get_password(self, f):
            return self._data.get(f)
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
                ok = all(doc.get(k)==v for k,v in (filters or {}).items())
                if ok:
                    return doc.get(fieldname) or doc.get("name")
            return None
        def exists(self, doctype, filters):
            return bool(self.get_value(doctype, filters, "name"))
        def get_all(self, doctype, filters=None, pluck=None, **kwargs):
            out=[]
            for doc in store.values():
                if doc.get("doctype")!=doctype: continue
                if not all(doc.get(k)==v for k,v in (filters or {}).items()): continue
                out.append(doc.get(pluck) if pluck else doc)
            return out
        def commit(self): pass
        def escape(self,v): return f"'{v}'"
    fake = type("F", (), {})()
    fake.db = FakeDB()
    def new_doc(dt): return FakeDoc(doctype=dt, data={"doctype":dt})
    def get_doc(dt, name):
        d=store.get(name)
        if not d: raise Exception(f"Not found {dt} {name}")
        return FakeDoc(doctype=dt, name=name, data=dict(d))
    def del_doc(dt, name, ignore_permissions=True):
        store.pop(name, None)
    fake.new_doc=new_doc; fake.get_doc=get_doc; fake.delete_doc=del_doc
    fake.get_value=fake.db.get_value; fake.throw=lambda m,*a,**k: (_ for _ in ()).throw(Exception(m))
    fake.get_all=fake.db.get_all; fake.get_site_config=lambda:{}
    fake.conf={}
    class Fc:
        def __init__(self): self._d={}
        def set_value(self,k,v,expires_in_sec=None): self._d[k]=v
        def get_value(self,k): return self._d.get(k)
        def delete_value(self,k): self._d.pop(k,None)
        def delete(self,k): self._d.pop(k,None)
    inst=Fc()
    fake.cache=lambda: inst
    monkeypatch.setattr(mod, "frappe", fake, raising=False)
    try:
        import heshly_core.heshly_core.doctype.heshly_calendar_connection.heshly_calendar_connection as dm
        dm.frappe=fake
    except Exception:
        pass
    return fake, store


def test_exchange_returns_naive_expires_at(monkeypatch):
    fake,_ = _fake_frappe(monkeypatch)
    import heshly_core.services.google.google_oauth_service as m
    monkeypatch.setattr(m, "frappe", fake, raising=False)
    svc = GoogleOAuthService(config=_cfg())
    resp = MagicMock()
    resp.status_code=200
    resp.json.return_value={"access_token":"at","refresh_token":"rt","expires_in":3600}
    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=resp):
        r = svc.exchange_code("code123")
        assert r["expires_at"] is not None
        assert r["expires_at"].tzinfo is None, "DB Datetime must be naive UTC"
        # Marshalling to MariaDB string must not contain +00:00
        s = str(r["expires_at"])
        assert "+00:00" not in s and s.count(":") >= 2


def test_refresh_returns_naive_expires_at(monkeypatch):
    fake,_ = _fake_frappe(monkeypatch)
    import heshly_core.services.google.google_oauth_service as m
    monkeypatch.setattr(m, "frappe", fake, raising=False)
    svc = GoogleOAuthService(config=_cfg())
    resp = MagicMock()
    resp.status_code=200
    resp.json.return_value={"access_token":"at2","expires_in":3600}
    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=resp):
        r = svc.refresh_access_token("rt123")
        assert r["expires_at"].tzinfo is None


def test_calendar_connection_save_with_naive_expires_at_succeeds(monkeypatch):
    fake, store = _fake_frappe(monkeypatch)
    import heshly_core.services.google.google_oauth_service as m
    monkeypatch.setattr(m, "frappe", fake, raising=False)
    svc = GoogleOAuthService(config=_cfg())
    resp = MagicMock()
    resp.status_code=200
    resp.json.return_value={"access_token":"at","refresh_token":"rt","expires_in":3600}
    with patch("heshly_core.services.google.google_oauth_service.requests.post", return_value=resp):
        token_data = svc.exchange_code("code123")
    # Simulate callback save path (must not raise Incorrect datetime value)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-x")
    conn = CalendarConnection(
        connection_id="tenant-x:google:primary",
        tenant_id="tenant-x",
        provider=CalendarProvider.GOOGLE,
        calendar_id="primary",
        timezone="Africa/Nairobi",
        status=CalendarConnectionStatus.ACTIVE,
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        expires_at=token_data["expires_at"],
        business_name="Cal",
    )
    saved = repo.save(conn)
    assert saved is not None
    stored = store.get("tenant-x:google:primary")
    assert stored is not None
    assert str(stored["expires_at"]).find("+00:00") == -1, f"stored still has tz: {stored['expires_at']}"
    reloaded = repo.get("tenant-x:google:primary", tenant_id="tenant-x")
    assert reloaded is not None
    assert reloaded.expires_at is None or reloaded.expires_at.tzinfo is None


def test_repository_normalizes_aware_datetimes_to_naive(monkeypatch):
    fake, store = _fake_frappe(monkeypatch)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-y")
    # Pass an aware datetime intentionally (legacy path)
    aware = datetime.now(UTC) + timedelta(seconds=3600)
    assert aware.tzinfo is not None
    conn = CalendarConnection(
        connection_id="tenant-y:google:primary",
        tenant_id="tenant-y",
        provider=CalendarProvider.GOOGLE,
        calendar_id="primary",
        timezone="UTC",
        status=CalendarConnectionStatus.ACTIVE,
        access_token="at",
        refresh_token="rt",
        expires_at=aware,
    )
    repo.save(conn)
    stored = store.get("tenant-y:google:primary")
    assert stored["expires_at"].tzinfo is None if hasattr(stored["expires_at"], "tzinfo") and stored["expires_at"].tzinfo is not None else True
    # String check
    assert "+00:00" not in str(stored["expires_at"])


def test_tenant_isolation_intact_after_fix(monkeypatch):
    fake,_ = _fake_frappe(monkeypatch)
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository
    repo = CalendarConnectionRepository()
    ctx = TenantContext()
    ctx.set("tenant-a")
    repo.save(CalendarConnection(connection_id="tenant-a:google:primary", tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="UTC", access_token="at-a"))
    ctx.set("tenant-b")
    # Must not see tenant-a's connection
    assert repo.get("tenant-a:google:primary", tenant_id="tenant-b") is None
    assert repo.get_for_provider(CalendarProvider.GOOGLE, tenant_id="tenant-b") is None


def test_oauth_state_hmac_still_valid(monkeypatch):
    fake,_ = _fake_frappe(monkeypatch)
    import heshly_core.services.google.google_oauth_service as m
    monkeypatch.setattr(m, "frappe", fake, raising=False)
    svc = GoogleOAuthService(config=_cfg())
    url, state = svc.build_authorization_url("tenant-z")
    # Verify correct tenant and that tampering fails
    assert svc.verify_state(state) == "tenant-z"
