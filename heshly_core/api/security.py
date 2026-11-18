from __future__ import annotations

import frappe


@frappe.whitelist()
def change_password(current_password: str | None = None, new_password: str | None = None, confirm_password: str | None = None, **_kw):
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    current_password = (current_password or "").strip()
    new_password = (new_password or "").strip()
    confirm_password = (confirm_password or "").strip()
    if not current_password:
        frappe.throw("Current password is required.")
    if not new_password:
        frappe.throw("New password is required.")
    if confirm_password and new_password != confirm_password:
        frappe.throw("New password and confirmation do not match.")
    if len(new_password) < 8:
        frappe.throw("New password must be at least 8 characters.")

    # Verify current password
    try:
        frappe.local.login_manager.check_password(frappe.session.user, current_password)
    except Exception:
        frappe.throw("Current password is incorrect.")

    # Use Frappe core update_password with old_password verification
    from frappe.core.doctype.user.user import update_password

    update_password(new_password=new_password, old_password=current_password, logout_all_sessions=0)
    return {"ok": True}
