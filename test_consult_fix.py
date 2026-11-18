import frappe
frappe.init(site="erp.heshly.com", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
from heshly_core.services.network.consultation_engine import _detect_domain, upsert_task_from_message, next_consultation_step
from heshly_core.services.network.qualification_service import qualify_message

# Test 3 fix: farming detail should not be hijacked
print("1. _is_farming_detail for borehole water:", end=" ")
from heshly_core.services.network.consultation_engine import _is_farming_detail
print(_is_farming_detail("I have 2 acres near Witu, borehole water, budget 800k, 12 months runway"))

print("2. _detect_domain for farming detail with borehole service:", _detect_domain("I have 2 acres near Witu, borehole water, budget 800k, 12 months runway", "borehole services"))
print("3. qualify _extract_open_service for farming multi-fact:", end=" ")
from heshly_core.services.network.qualification_service import _extract_open_service
print(_extract_open_service("I have 2 acres near Witu, borehole water, budget 800k, 12 months runway", None))
print("4. qualify with farming existing crop:", _extract_open_service("I have 2 acres near Witu, borehole water, budget 800k, 12 months runway", "smartphone"))
print("5. product camera:", _extract_open_service("64GB storage, good camera, Nairobi delivery", "smartphone"))
print("6. product camera without existing:", _extract_open_service("64GB storage, good camera, Nairobi delivery", None))

# Full farming sequence with fixes
print("\n=== FULL FARMING SEQUENCE ===")
qd = {}
for txt in ["Is it a good idea to move to Lamu for farming?", "Maize", "I have 2 acres near Witu, borehole water, budget 800k, 12 months runway"]:
    ext = qualify_message(txt, {})
    # Use the farming-aware location fix: _is_farming_detail check happens inside upsert
    t, all_tasks, qd = upsert_task_from_message(txt, qd, ext)
    q, a = next_consultation_step(t)
    print(f"  {txt[:40]!r} -> domain={t.domain} svc={t.requested_service!r} loc={t.location!r} facts={t.facts} next_q={q[:60] if q else 'ASSESS:'+(a[:40] if a else 'none')}")

