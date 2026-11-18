import frappe
def get_context(context):
    try:
        doc=frappe.get_doc("Heshly Website Page", {"route": frappe.form_dict.get("route") or frappe.request.path.strip("/")})
        context.page_doc=doc
    except Exception:
        context.page_doc=None
    return context
