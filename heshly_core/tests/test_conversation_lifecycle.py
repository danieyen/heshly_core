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

def _qual(r): return r.get("qualification") or {}
def _reply(r): return (r.get("reply") or "").lower()

class TestLifecycleContinuity:
    def test_retains_context_across_followups(self):
        sid=_sid()
        r1=_call("I need a person to do my laundry.", sid)
        sid=r1.get("session_id") or sid
        _call("Niko hapa Kipsebwo, Nandi Hills.", sid)
        r=_call("Hello?", sid)
        assert _qual(r).get("requested_service")=="laundry"
        assert _qual(r).get("location")=="Kipsebwo, Nandi Hills"

class TestNewChat:
    def test_new_chat_no_inherited(self):
        from heshly_core.api.website_chat import clear_conversation
        sid=_sid()
        r1=_call("I need a person to do my laundry.", sid)
        sid=r1.get("session_id") or sid
        _call("Kipsebwo, Nandi Hills", sid)
        res=clear_conversation(session_id=sid, new_session=True)
        new_sid=res.get("session_id")
        assert new_sid and new_sid != sid
        # new session should be empty
        r= _call("Hi", new_sid)
        assert _qual(r).get("requested_service")==""
        assert _qual(r).get("location")==""

class TestClearConversation:
    def test_clear_removes_active_context(self):
        from heshly_core.api.website_chat import clear_conversation, get_conversation
        sid=_sid()
        r1=_call("I need a person to do my laundry.", sid)
        sid=r1.get("session_id") or sid
        _call("Kipsebwo, Nandi Hills", sid)
        clear_conversation(session_id=sid)
        r=_call("Hi", sid)
        # After clear, same sid should not have old service (clear cancelled the row, next call creates fresh)
        assert _qual(r).get("requested_service")==""

    def test_clear_does_not_delete_other_sessions(self):
        from heshly_core.api.website_chat import clear_conversation
        s1=_sid(); s2=_sid()
        r1=_call("I need a plumber in Westlands", s1)
        s1=r1.get("session_id") or s1
        r2=_call("I need a person to do my laundry.", s2)
        s2=r2.get("session_id") or s2
        _call("Kipsebwo, Nandi Hills", s2)
        clear_conversation(session_id=s1)
        r=_call("Hello?", s2)
        assert _qual(r).get("requested_service")=="laundry"

class TestExplicitReset:
    def test_reset_phrases(self):
        for phrase in ["Start again", "New chat", "Forget this request", "Anza upya", "Tusianze na hiyo tena"]:
            sid=_sid()
            r1=_call("I need a person to do my laundry.", sid)
            sid=r1.get("session_id") or sid
            _call("Kipsebwo, Nandi Hills", sid)
            r=_call(phrase, sid)
            assert _qual(r).get("qualification_state")=="pending" or _qual(r).get("requested_service")=="", f"reset failed for {phrase}: {_qual(r)}"

class TestNewServiceWithoutReset:
    def test_updates_intent(self):
        sid=_sid()
        r1=_call("I need a person to do my laundry.", sid)
        sid=r1.get("session_id") or sid
        _call("Kipsebwo, Nandi Hills", sid)
        r=_call("Actually, I need a plumber.", sid)
        assert _qual(r).get("requested_service")=="plumbing"
        assert "laundry" not in _qual(r).get("requested_service","").lower()

class TestDeletedNotRestored:
    def test_cleared_not_auto_restored(self):
        from heshly_core.api.website_chat import clear_conversation, get_conversation
        sid=_sid()
        r1=_call("I need a person to do my laundry.", sid)
        sid=r1.get("session_id") or sid
        _call("Kipsebwo, Nandi Hills", sid)
        clear_conversation(session_id=sid)
        conv=get_conversation(session_id=sid)
        turns=conv.get("turns") or []
        # After clear, old turns should be gone (new row empty until next Hi)
        assert len(turns)==0 or all(t.get("message","").lower() not in ("kipsebwo") for t in turns[-2:])

class TestIsolation:
    def test_isolated(self):
        s1=_sid(); s2=_sid()
        _call("I need a plumber in Westlands", s1)
        _call("I need a person to do my laundry.", s2)
        _call("Leaking pipe", s1)
        r=_call("Hello?", s2)
        assert _qual(r).get("requested_service")=="laundry"

class TestLaundryContinue:
    def test_laundry_still_works(self):
        sid=_sid()
        _call("Hi", sid)
        r=_call("I need a person to do my laundry.", sid)
        sid=r.get("session_id") or sid
        _call("Niko hapa Kipsebwo, Nandi Hills.", sid)
        r=_call("Hello?", sid)
        assert _qual(r).get("requested_service")=="laundry"
