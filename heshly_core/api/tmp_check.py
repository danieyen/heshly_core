def run():
    import frappe
    frappe.init(site="erp.heshly.com", sites_path="/home/frappe/frappe-bench/sites"); frappe.connect()
    from heshly_core.api.website_chat import website_chat
    import uuid
    for name, msgs in [
        ("PLUMB_WESTLANDS_ISSUE", ["I need a plumber in Westlands. My budget is KSh 2,500. You got someone?", "Leaking pipe under the sink"]),
        ("PLUMB_THEN_LAMU_FARM", ["I need a plumber in Westlands. My budget is 2500.", "While still at it, I would like to know if it is a great idea to move to Lamu for farming.", "Maize, borehole water near Witu"]),
        ("FARM_STANDALONE", ["Is it a good idea to move to Lamu for farming?"]),
        ("FARM_MAIZE_ONLY", ["Is it a good idea to move to Lamu for farming?", "Maize"]),
        ("PRODUCT_PHONE", ["I need a smartphone for photography. Budget 900 KES.", "64GB, good camera, Nairobi delivery"]),
    ]:
        print(f"\n===== {name} =====")
        sid="hweb_"+uuid.uuid4().hex[:10]
        for m in msgs:
            res=website_chat(message=m, session_id=sid); sid=res.get("session_id") or sid
            print(">", repr(m[:60]), "\n ->", repr((res.get("reply") or "")[:500]))
        print("---")
    return {"done": True}
