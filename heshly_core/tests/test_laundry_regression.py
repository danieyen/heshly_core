from __future__ import annotations
import uuid

def _call(message: str, session_id: str | None = None):
    from heshly_core.api.website_chat import website_chat
    kwargs = {"message": message}
    if session_id:
        kwargs["session_id"] = session_id
    res = website_chat(**kwargs)
    assert isinstance(res, dict)
    return res

def _sid():
    return f"hweb_{uuid.uuid4().hex[:12]}"

def _reply(r):
    return (r.get("reply") or r.get("message") or "").strip()

def _qual(r):
    return r.get("qualification") or {}

class TestLaundryBugfix:
    def test_full_laundry_flow(self):
        sid = _sid()
        r1 = _call("Hi", sid)
        sid = r1.get("session_id") or sid
        assert r1.get("success")
        r2 = _call("I need a person to do my laundry.", sid)
        sid = r2.get("session_id") or sid
        assert _qual(r2).get("requested_service") == "laundry"
        r3 = _call("Niko hapa Kipsebwo, Nandi Hills.", sid)
        sid = r3.get("session_id") or sid
        assert _qual(r3).get("location") == "Kipsebwo, Nandi Hills"
        assert _qual(r3).get("requested_service") == "laundry"
        assert "where" not in _reply(r3).lower() or "laundry" in _reply(r3).lower()
        r4 = _call("Hello?", sid)
        assert _qual(r4).get("location") == "Kipsebwo, Nandi Hills"
        assert _qual(r4).get("requested_service") == "laundry"
        assert "Kipsebwo" in _reply(r4) or "laundry" in _reply(r4).lower()
        r5 = _call("Are you there?", sid)
        assert _qual(r5).get("requested_service") == "laundry"
        r6 = _call("Wash lady at Kipsebwo in Nandi Hills.", sid)
        assert _qual(r6).get("requested_service") == "laundry"
        assert "help you today" not in _reply(r6).lower() or "laundry" in _reply(r6).lower()
        r7 = _call("I'm in Nandi Hills", sid)
        assert _qual(r7).get("location") == "Kipsebwo, Nandi Hills"
        assert _qual(r7).get("requested_service") == "laundry"

    def test_swahili_mtu_wa_kufua(self):
        r = _call("mtu wa kufua nguo", _sid())
        assert _qual(r).get("requested_service") == "laundry"

    def test_presence_does_not_wipe(self):
        sid = _sid()
        r1 = _call("I need a person to do my laundry.", sid)
        sid = r1.get("session_id") or sid
        _call("Kipsebwo, Nandi Hills", sid)
        r = _call("Hello?", sid)
        assert _qual(r).get("requested_service") == "laundry"
        assert _qual(r).get("location") == "Kipsebwo, Nandi Hills"

    def test_broad_town_retains_specific(self):
        sid = _sid()
        r1 = _call("I need a person to do my laundry.", sid)
        sid = r1.get("session_id") or sid
        _call("Kipsebwo, Nandi Hills", sid)
        r = _call("I'm in Nandi Hills", sid)
        assert _qual(r).get("location") == "Kipsebwo, Nandi Hills"

    def test_session_isolation(self):
        import frappe
        s1 = _sid()
        s2 = _sid()
        _call("I need a plumber in Nairobi", s1)
        _call("I need a person to do my laundry.", s2)
        _call("Westlands", s1)
        _call("Niko hapa Kipsebwo, Nandi Hills.", s2)
        r1 = _call("Leaking pipe", s1)
        r2 = _call("Hello?", s2)
        assert _qual(r1).get("requested_service") == "plumbing"
        assert _qual(r2).get("requested_service") == "laundry"
