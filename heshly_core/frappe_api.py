import frappe


@frappe.whitelist(allow_guest=True)
def ping():
    return {
        "status": "ok",
        "product": "Heshly",
        "version": "0.0.1"
    }
