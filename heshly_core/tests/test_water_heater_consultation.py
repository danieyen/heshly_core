import uuid
import frappe

def _sid():
    return f"hweb_{uuid.uuid4().hex[:12]}"

def _ensure_site():
    try:
        frappe.init(site="erp.heshly.com", sites_path="/home/frappe/frappe-bench/sites")
        frappe.connect()
    except Exception:
        try:
            frappe.local.site  # type: ignore
        except Exception:
            pass

_ensure_site()
from heshly_core.api.website_chat import website_chat

def test_water_heater_not_heating_specific():
    _ensure_site()
    s=_sid()
    r=website_chat({"message":"My water heater is not heating.","session_id":s})
    reply=(r.get("reply") or "")
    assert "completely cold" in reply.lower() or "run out" in reply.lower(), f"expected specific water-heater question, got {reply[:300]}"
    assert "What exactly is going wrong, in your own words" not in reply
    assert "My water heater is not heating. What exactly" not in reply

def test_water_heater_followup_cold():
    _ensure_site()
    s=f"hweb_{uuid.uuid4().hex[:12]}"
    website_chat({"message":"My water heater is not heating.","session_id":s})
    r=website_chat({"message":"completely cold","session_id":s})
    reply=(r.get("reply") or "")
    assert "electric" in reply.lower() or "gas" in reply.lower() or "solar" in reply.lower()

def test_water_heater_followup_runs_out():
    _ensure_site()
    s=_sid()
    website_chat({"message":"My water heater is not heating.","session_id":s})
    r=website_chat({"message":"it heats but runs out quickly","session_id":s})
    reply=(r.get("reply") or "")
    assert "run out" in reply.lower() or "every time" in reply.lower()
    assert "What exactly is going wrong" not in reply

def test_safety_sparks_water_heater():
    _ensure_site()
    s=_sid()
    r=website_chat({"message":"My water heater has sparks","session_id":s})
    reply=(r.get("reply") or "").lower()
    assert "sparks" in reply or "hazard" in reply or "stop using" in reply

def test_not_generic_across_home_services():
    _ensure_site()
    cases=["My toilet is blocked.","My kitchen sink is leaking.","My AC is running but it is not cooling.","There are sparks coming from my wall socket.","I have termites in my house.","My roof is leaking.","I need to repaint my house."]
    for msg in cases:
        s=_sid()
        r=website_chat({"message":msg,"session_id":s})
        assert "What exactly is going wrong, in your own words" not in (r.get("reply") or ""), f"generic fallback for {msg}: {(r.get('reply') or '')[:200]}"
