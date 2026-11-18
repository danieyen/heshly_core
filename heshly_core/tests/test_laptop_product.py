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

def _sid(): return f"hweb_{uuid.uuid4().hex[:12]}"

def _reply(r): return (r.get("reply") or "").strip()
def _qual(r): return r.get("qualification") or {}

class TestLaptopSwallowed:
    def test_exact_laptop_flow(self):
        sid=_sid()
        r1=_call("i'd like to buy a laptop. im just not sure which model to buy. can you help?", sid)
        sid=r1.get("session_id") or sid
        assert "what will you mainly use" in _reply(r1).lower()
        r2=_call("i want to use it for my coding projects and watching movies when Im bored", sid)
        assert "what do you need help with" not in _reply(r2).lower(), _reply(r2)
        assert len(_reply(r2)) > 30
        r3=_call("i need you to tell me the right machine that can handle that.", sid)
        assert "what do you need help with" not in _reply(r3).lower(), _reply(r3)
        assert len(_reply(r3)) > 30
        # Should have product recs or budget question, not swallowed
        assert r3.get("recommendations") or "budget" in _reply(r3).lower() or "laptop" in _reply(r3).lower()

    def test_product_without_budget(self):
        sid=_sid()
        _call("i'd like to buy a laptop.", sid)
        sid=_call("i'd like to buy a laptop.", sid).get("session_id") or sid
        r=_call("I need a laptop for programming.", sid)
        assert "what do you need help with" not in _reply(r).lower()

    def test_product_vs_service_routing(self):
        sid=_sid()
        r=_call("I need a laptop for programming.", sid)
        sid=r.get("session_id") or sid
        # laptop should not create plumbing dispatch
        assert "plumbing" not in (_qual(r).get("requested_service") or "").lower()
        sid2=_sid()
        r2=_call("I need a plumber in Westlands", sid2)
        assert _qual(r2).get("requested_service")=="plumbing"
