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

class TestLaptopThreeMsg:
    def test_persists_and_budget_question(self):
        sid=_sid()
        r1=_call("I'd like to buy a laptop. I'm just not sure which model to buy. Can you help?", sid)
        sid=r1.get("session_id") or sid
        assert "what will you mainly use" in _reply(r1).lower()
        r2=_call("I want to use it for my coding projects and watching movies when I'm bored", sid)
        # Should not be swallowed, should ask budget (honest demo catalogue)
        assert len(_reply(r2)) > 30
        assert "what do you need help with" not in _reply(r2).lower()
        assert "budget" in _reply(r2).lower() or "ksh" in _reply(r2).lower(), _reply(r2)
        r3=_call("I need you to tell me the right machine that can handle that.", sid)
        assert len(_reply(r3)) > 30
        assert "what do you need help with" not in _reply(r3).lower()
        # Third should still be budget or recommendation, not empty swallow
        assert _reply(r3) != ""

    def test_with_budget_then_recommend(self):
        sid=_sid()
        _call("I'd like to buy a laptop. I'm just not sure which model to buy. Can you help?", sid)
        _call("I want to use it for my coding projects and watching movies when I'm bored", sid)
        r=_call("My budget is 80000", sid)
        # With budget, should get catalogue (still demo but with budget it filters and shows Laptop)
        assert len(_reply(r)) > 30
        assert "what do you need help with" not in _reply(r).lower()

    def test_clears_not_contaminate(self):
        sid=_sid()
        r1=_call("I need a laptop for coding", sid)
        sid=r1.get("session_id") or sid
        from heshly_core.api.website_chat import clear_conversation
        clear_conversation(session_id=sid)
        r=_call("I need a plumber in Westlands", sid)
        assert (_qual(r).get("requested_service") or "") == "plumbing"
