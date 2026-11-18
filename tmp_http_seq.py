import frappe, json, sys, uuid
frappe.init("erp.heshly.com", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
sys.path.insert(0, "/home/frappe/frappe-bench/apps/heshly_core")
from heshly_core.api.website_chat import website_chat
sid="hweb_"+uuid.uuid4().hex[:12]
print("SID "+sid)
def step(msg):
    r=website_chat(payload=json.dumps({"message": msg, "session_id": sid}))
    print("USER "+msg)
    print(" reply "+r.get("reply","")[:90])
    print(" qual "+str(r.get("qualification")))
    return r.get("session_id", sid)
sid=step("yeah i'm looking for a house builder.")
import frappe as _f
phone="wa_web_"+sid.replace("hweb_","")[:12]
doc=_f.db.get_value("Heshly Network Conversation", {"customer_phone": phone, "channel":"web"}, ["name","qualification_data","requested_service","location"], as_dict=True, order_by="modified desc")
qd=json.loads(doc["qualification_data"] or "{}") if doc["qualification_data"] else {}
print(" DB "+str([(t.get("requested_service"),t.get("location")) for t in qd.get("consult_tasks",[])]))
print(" active "+str(qd.get("active_task_id","")[:8]))
sid=step("kasarani area. also i need a tile fixer.")
phone="wa_web_"+sid.replace("hweb_","")[:12]
doc=_f.db.get_value("Heshly Network Conversation", {"customer_phone": phone, "channel":"web"}, ["name","qualification_data","requested_service","location"], as_dict=True, order_by="modified desc")
qd=json.loads(doc["qualification_data"] or "{}") if doc["qualification_data"] else {}
print(" DB "+str([(t.get("requested_service"),t.get("location")) for t in qd.get("consult_tasks",[])]))
print(" active "+str(qd.get("active_task_id","")[:8]))
sid=step("also need an electrician")
phone="wa_web_"+sid.replace("hweb_","")[:12]
doc=_f.db.get_value("Heshly Network Conversation", {"customer_phone": phone, "channel":"web"}, ["name","qualification_data"], as_dict=True, order_by="modified desc")
qd=json.loads(doc["qualification_data"] or "{}") if doc["qualification_data"] else {}
print(" DB "+str([(t.get("requested_service"),t.get("location")) for t in qd.get("consult_tasks",[])]))
sid=step("actually make that a carpenter in kasarani")
phone="wa_web_"+sid.replace("hweb_","")[:12]
doc=_f.db.get_value("Heshly Network Conversation", {"customer_phone": phone, "channel":"web"}, ["name","qualification_data"], as_dict=True, order_by="modified desc")
qd=json.loads(doc["qualification_data"] or "{}") if doc["qualification_data"] else {}
print(" DB "+str([(t.get("requested_service"),t.get("location")) for t in qd.get("consult_tasks",[])]))
sid=step("tile fixer")
phone="wa_web_"+sid.replace("hweb_","")[:12]
doc=_f.db.get_value("Heshly Network Conversation", {"customer_phone": phone, "channel":"web"}, ["name","qualification_data"], as_dict=True, order_by="modified desc")
qd=json.loads(doc["qualification_data"] or "{}") if doc["qualification_data"] else {}
print(" DB "+str([(t.get("requested_service"),t.get("location")) for t in qd.get("consult_tasks",[])]))
print(" dup tile "+str(sum(1 for t in qd.get("consult_tasks",[]) if "tile" in t.get("requested_service","").lower())))
