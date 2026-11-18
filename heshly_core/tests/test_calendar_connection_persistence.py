from __future__ import annotations

import pytest
from datetime import datetime, UTC, timedelta

from heshly_core.models.calendar import CalendarProvider, CalendarConfiguration
from heshly_core.models.calendar_connection import CalendarConnection, CalendarConnectionStatus
from heshly_core.models.calendar_provider import ProviderConnection
from heshly_core.services.calendar.calendar_connection_service import CalendarConnectionService
from heshly_core.services.tenant.tenant_context import TenantContext

# Use fake frappe in-memory registry to avoid requiring bench
import frappe  # will be mocked via conftest mocker or stubbed fallback

try:
    import frappe as _frappe
    _has_frappe = bool(getattr(_frappe, "db", None))
except Exception:
    _has_frappe = False


def _get_repo_with_fake_db(monkeypatch):
    from heshly_core.repositories.calendar_connection_repository import CalendarConnectionRepository

    # Force fake DB for this test suite so it never touches a real bench DB
    # (bench not available in CI). If you want to test against real frappe,
    # set HESHLY_TEST_REAL_FRAPPE=1.
    import os

    if _has_frappe and os.getenv("HESHLY_TEST_REAL_FRAPPE") == "1":
        try:
            _frappe.db.get_value  # type: ignore
            repo = CalendarConnectionRepository()
            return repo, {}
        except Exception:
            pass

    # Stub frappe db
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
            # store via outer closure
            store[self._data["name"]] = dict(self._data)
            store[self._data["name"]]["doctype"] = self.doctype

        def update(self, d):
            self._data.update(d)

    store: dict[str, dict] = {}

    class FakeDB:
        def get_value(self, doctype, filters, fieldname="name"):
            for key, doc in list(store.items()):
                if doc.get("doctype") != doctype:
                    continue
                match = True
                for fk, fv in (filters or {}).items():
                    if doc.get(fk) != fv:
                        match = False
                        break
                if match:
                    return doc.get(fieldname) or doc.get("name")
            return None

        def exists(self, doctype, filters):
            return bool(self.get_value(doctype, filters, "name"))

        def get_all(self, doctype, filters=None, pluck=None):
            out = []
            for doc in store.values():
                if doc.get("doctype") != doctype:
                    continue
                match = True
                for fk, fv in (filters or {}).items():
                    if doc.get(fk) != fv:
                        match = False
                        break
                if match:
                    out.append(doc.get(pluck) if pluck else doc)
            return out

        def commit(self):
            pass

        def escape(self, v):
            return f"'{v}'"

    fake_frappe = type("F", (), {})()
    fake_frappe.db = FakeDB()  # type: ignore

    def fake_new_doc(doctype):
        return FakeDoc(doctype=doctype, data={"doctype": doctype})

    def fake_get_doc(doctype, name):
        doc = store.get(name)
        if not doc:
            raise Exception(f"Not found {doctype} {name}")
        return FakeDoc(doctype=doctype, name=name, data=dict(doc))

    def fake_delete_doc(doctype, name, ignore_permissions=True):
        if name in store:
            del store[name]

    def fake_get_value(doctype, filters, fieldname="name"):
        return fake_frappe.db.get_value(doctype, filters, fieldname)

    def fake_throw(msg):
        raise Exception(msg)

    # frappe.get_all is used by repo.list(); support both frappe.get_all and frappe.db.get_all patterns
    def fake_get_all(doctype, filters=None, pluck=None, **kwargs):
        return fake_frappe.db.get_all(doctype, filters=filters, pluck=pluck)

    fake_frappe.get_all = fake_get_all  # type: ignore

    # monkeypatch frappe module used by repository
    import heshly_core.repositories.calendar_connection_repository as mod

    monkeypatch.setattr(mod, "frappe", fake_frappe, raising=False)

    # also need to handle frappe.new_doc etc inside repo
    fake_frappe.new_doc = fake_new_doc  # type: ignore
    fake_frappe.get_doc = fake_get_doc  # type: ignore
    fake_frappe.delete_doc = fake_delete_doc  # type: ignore
    fake_frappe.get_value = fake_get_value  # type: ignore
    fake_frappe.throw = fake_throw  # type: ignore

    # Doctype patch is optional (bench-only); skip if frappe.model unavailable
    try:
        import heshly_core.heshly_core.doctype.heshly_calendar_connection.heshly_calendar_connection as dtype_mod

        dtype_mod.frappe = fake_frappe  # type: ignore
    except Exception:
        pass

    return CalendarConnectionRepository(), store

    # return repo


def _make_conn(tenant_id="tenant-a", provider=CalendarProvider.GOOGLE, cal_id="primary", business_name="Display Biz"):
    return CalendarConnection(
        connection_id=f"{tenant_id}:{provider.value}:{cal_id}",
        tenant_id=tenant_id,
        provider=provider,
        calendar_id=cal_id,
        timezone="Africa/Nairobi",
        status=CalendarConnectionStatus.ACTIVE,
        access_token="tok123",
        refresh_token="ref123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        business_name=business_name,
    )


def test_save_and_get_tenant_scoped(monkeypatch):
    ctx = TenantContext()
    ctx.set("tenant-a")
    repo, _ = _get_repo_with_fake_db(monkeypatch)
    svc = CalendarConnectionService(repository=repo, tenant_context=ctx)
    conn = _make_conn("tenant-a")
    saved = svc.save(conn)
    assert saved.tenant_id == "tenant-a"
    retrieved = svc.get(saved.connection_id)
    assert retrieved is not None
    assert retrieved.tenant_id == "tenant-a"
    assert retrieved.business_name == "Display Biz"  # display-only preserved
    assert retrieved.access_token == "tok123"


def test_tenant_isolation_list_and_cross_access_blocked(monkeypatch):
    ctx_a = TenantContext()
    ctx_a.set("tenant-a")
    repo, _ = _get_repo_with_fake_db(monkeypatch)
    svc_a = CalendarConnectionService(repository=repo, tenant_context=ctx_a)
    svc_a.save(_make_conn("tenant-a", CalendarProvider.GOOGLE, "primary"))
    svc_a.save(_make_conn("tenant-a", CalendarProvider.OUTLOOK, "primary2"))

    # Switch to tenant-b context: should not see tenant-a data
    ctx_b = TenantContext()
    ctx_b.set("tenant-b")
    svc_b = CalendarConnectionService(repository=repo, tenant_context=ctx_b)
    assert svc_b.list() == []
    assert svc_b.get("tenant-a:google:primary") is None  # filtered by tenant

    # Cross-tenant save with mismatched tenant_id must raise
    bad = _make_conn("tenant-b", provider=CalendarProvider.GOOGLE, cal_id="new")
    # Force mismatch: context is tenant-b but try to save tenant-a's connection id
    attacker = CalendarConnection(
        connection_id="tenant-a:google:primary",
        tenant_id="tenant-a",
        provider=CalendarProvider.GOOGLE,
        calendar_id="primary",
        timezone="Africa/Nairobi",
        business_name="Hacker Biz",
    )
    # repository.save with tenant-a while context is tenant-b should fail via require_tenant
    with pytest.raises((PermissionError, ValueError, RuntimeError, Exception)):
        svc_b.save(attacker)


def test_provider_connection_conversion_roundtrip():
    cfg = CalendarConfiguration(
        provider=CalendarProvider.GOOGLE, calendar_id="primary", timezone="Africa/Nairobi", tenant_id="tenant-x", business_name="My Biz"
    )
    pc = ProviderConnection(configuration=cfg, access_token="at", refresh_token="rt", expires_at=datetime.now(UTC) + timedelta(hours=2))
    cc = CalendarConnection.from_provider_connection("tenant-x:google:primary", pc)
    assert cc.tenant_id == "tenant-x"
    assert cc.calendar_id == "primary"
    assert cc.provider == CalendarProvider.GOOGLE
    pc2 = cc.to_provider_connection()
    assert pc2.configuration.tenant_id == "tenant-x"
    assert pc2.access_token == "at"
    assert pc2.configuration.business_name == "My Biz"


def test_update_tokens_tenant_isolated(monkeypatch):
    ctx = TenantContext()
    ctx.set("tenant-a")
    repo, _ = _get_repo_with_fake_db(monkeypatch)
    svc = CalendarConnectionService(repository=repo, tenant_context=ctx)
    conn = _make_conn("tenant-a")
    svc.save(conn)
    new_exp = datetime.now(UTC) + timedelta(hours=5)
    updated = svc.update_tokens(conn.connection_id, access_token="new_at", expires_at=new_exp)
    assert updated is not None
    assert updated.access_token == "new_at"
    # Repository normalizes to naive UTC for MariaDB Datetime fields
    expected_naive = new_exp.replace(tzinfo=None)
    assert updated.expires_at == expected_naive
    assert updated.expires_at.tzinfo is None

    # Other tenant cannot update
    ctx_b = TenantContext()
    ctx_b.set("tenant-b")
    svc_b = CalendarConnectionService(repository=repo, tenant_context=ctx_b)
    assert svc_b.update_tokens(conn.connection_id, access_token="hacked") is None


def test_business_name_display_only_not_tenant_identifier():
    # Ensure CalendarConfiguration business_name is not used for tenant resolution
    cfg = CalendarConfiguration(
        provider=CalendarProvider.GOOGLE, calendar_id="c1", timezone="Africa/Nairobi", tenant_id="real-tenant", business_name="Fake Biz Name"
    )
    pc = ProviderConnection(configuration=cfg, access_token="tok", refresh_token="ref")
    cc = CalendarConnection.from_provider_connection("real-tenant:google:c1", pc)
    assert cc.tenant_id == "real-tenant"
    assert cc.business_name == "Fake Biz Name"
    # tenant_id must not equal business_name
    assert cc.tenant_id != cc.business_name


def test_no_oauth_in_n8n_tokens_owned_by_core(monkeypatch):
    # Tokens are stored in repository; API exposes only has_* flags in list()
    from heshly_core.api.calendar_connection_api import CalendarConnectionAPI

    ctx = TenantContext()
    ctx.set("tenant-a")
    repo, _ = _get_repo_with_fake_db(monkeypatch)
    svc = CalendarConnectionService(repository=repo, tenant_context=ctx)
    api = CalendarConnectionAPI(tenant_context=ctx, service=svc)
    api.save(
        {
            "connection_id": "tenant-a:google:primary",
            "provider": "google",
            "calendar_id": "primary",
            "timezone": "Africa/Nairobi",
            "access_token": "secret_at",
            "refresh_token": "secret_rt",
            "business_name": "My Biz",
        }
    )
    lst = api.list({})
    assert lst["success"] is True
    assert lst["connections"][0]["has_access_token"] is True
    assert lst["connections"][0]["has_refresh_token"] is True
    # raw tokens must not appear in list payload
    assert "access_token" not in str(lst) or "secret_at" not in str(lst)
