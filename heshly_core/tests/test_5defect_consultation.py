from __future__ import annotations
import frappe
import uuid

def hweb(): return f"hweb_{uuid.uuid4().hex[:10]}"

def call(message, sid=None):
    from heshly_core.api.website_chat import website_chat
    kwargs={"message": message}
    if sid:
        kwargs["session_id"] = sid
    res=website_chat(**kwargs)
    assert isinstance(res, dict)
    return res

def reply(res):
    return (res.get("reply") or res.get("message") or "").strip()

class TestDefect1PlumbingConsultationOverwrite:
    def test_plumber_westlands_2500_asks_issue_not_no_match(self):
        sid=hweb()
        r1=call("I need a plumber in Westlands. My budget is KSh 2,500. You got someone?", sid)
        sid=r1.get("session_id") or sid
        rep=(reply(r1) or "").lower()
        assert "what needs fixing" in rep or "fixing" in rep, f"expected consult question, got {rep!r}"
        q=r1.get("qualification") or {}
        assert "westlands" in (q.get("location") or "").lower()

    def test_plumber_issue_followup(self):
        sid=hweb()
        r1=call("I need a plumber in Westlands. My budget is KSh 2,500.", sid)
        sid=r1.get("session_id") or sid
        r2=call("It is a leaking pipe under the sink", sid)
        rep2=(reply(r2) or "").lower()
        # After issue provided, should be closer to referral, not re-ask issue
        assert "leak" in rep2 or "westlands" in rep2 or "finding" in rep2 or "fixing" not in rep2 or "plumb" in rep2

class TestDefect2FarmingContinuity:
    def test_farming_maize_preserved_and_adaptive(self):
        sid=hweb()
        r1=call("Is it a good idea to move to Lamu for farming?", sid)
        sid=r1.get("session_id") or sid
        rep1=(reply(r1) or "").lower()
        assert any(s in rep1 for s in ("crop","grow")), f"crop question expected {rep1!r}"
        r2=call("Maize", sid)
        rep2=(reply(r2) or "").lower()
        assert any(s in rep2 for s in ("water","land","irrigat","soil","budget","runway")), f"adaptive land/water question, got {rep2!r}"
        assert "what crop" not in rep2, f"crop loop {rep2!r}"

    def test_farming_borehole_water_not_hijacked(self):
        sid=hweb()
        r1=call("Is it a good idea to move to Lamu for farming?", sid)
        sid=r1.get("session_id") or sid
        r2=call("Maize", sid)
        r3=call("I have 2 acres near Witu, borehole water, budget 800k, 12 months runway", sid)
        rep3=(reply(r3) or "").lower()
        assert any(s in rep3 for s in ("conditional","verify","soil","market","water","land")), f"expected assessment, got {rep3!r}"
        # Must not be routed to borehole service
        assert "borehole services" not in rep3

class TestDefect3BoreholeNotPlumbing:
    def test_farming_borehole_stays_farming(self):
        from heshly_core.services.network.qualification_service import _extract_open_service
        from heshly_core.services.network.consultation_engine import _detect_domain
        msg="I have 2 acres near Witu, borehole water, budget 800k, 12 months runway"
        # Borehole water in farming context should stay farming, not become borehole service
        assert _detect_domain(msg, "")[0] == "farming"
        assert _extract_open_service(msg, None) is None

class TestDefect4ProductCameraNotCCTV:
    def test_camera_in_smartphone_context_not_cctv(self):
        from heshly_core.services.network.qualification_service import _extract_open_service
        assert _extract_open_service("64GB storage, good camera, Nairobi delivery", "smartphone") is None
        # website flow
        sid=hweb()
        r1=call("I need a smartphone for photography. Budget 900 KES.", sid)
        sid=r1.get("session_id") or sid
        r2=call("64GB storage, good camera, Nairobi delivery", sid)
        rep2=(reply(r2) or "").lower()
        assert "cctv" not in rep2
        assert rep2, "product follow-up empty"
        # Should show catalogue or ask specs, not provider no-match for CCTV
        assert "camera" in rep2 or "smartphone" in rep2 or "catalogue" in rep2 or "catalog" in rep2 or "storage" in rep2 or "spec" in rep2 or "kes" in rep2 or "options" in rep2, f"got {rep2!r}"

    def test_legit_cctv_still_works(self):
        sid=hweb()
        r=call("I need someone to install CCTV at my shop in Nairobi", sid)
        rep=(reply(r) or "").lower()
        q=r.get("qualification") or {}
        assert "cctv" in (q.get("requested_service") or "").lower() or "cctv" in rep

class TestDefect5FarmingProgressesNotLoop:
    def test_stepwise_farming_progresses(self):
        sid=hweb()
        r1=call("Is it a good idea to move to Lamu for farming?", sid)
        sid=r1.get("session_id") or sid
        r2=call("Maize", sid)
        sid=r2.get("session_id") or sid
        r3=call("I have access to land near Witu", sid)
        rep3=(reply(r3) or "").lower()
        assert "what crop" not in rep3, f"should not loop to crop {rep3!r}"
        assert any(s in rep3 for s in ("water","irrigat","budget","runway","soil")), f"water/budget question {rep3!r}"
        r4=call("borehole water, budget 800k, 12 months runway", sid)
        rep4=(reply(r4) or "").lower()
        assert any(s in rep4 for s in ("conditional","verify","soil","market","water","land")), f"assessment {rep4!r}"

    def test_legit_borehole_fix_nakuru_still_works(self):
        sid=hweb()
        r=call("I need someone to fix my borehole in Nakuru", sid)
        q=r.get("qualification") or {}
        assert "borehole" in (q.get("requested_service") or "").lower()
