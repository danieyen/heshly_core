from __future__ import annotations

import re

import frappe

SUPPORTED_TIMEZONES = {
    "Africa/Nairobi",
    "Africa/Cairo",
    "Africa/Johannesburg",
    "Africa/Lagos",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Asia/Singapore",
    "America/New_York",
    "America/Los_Angeles",
    "UTC",
}
SUPPORTED_CURRENCIES = {"KES", "USD", "EUR", "GBP", "AED", "ZAR", "INR", "SGD"}


def _require_business():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    bid = frappe.session.data.get("heshly_business_id")
    if not bid:
        frappe.throw("Business session not found.", frappe.PermissionError)
    biz = frappe.db.get_value(
        "Business Account",
        {"business_id": bid, "status": "Active"},
        ["name", "business_id", "business_name", "tenant_id", "domain", "status", "industry", "location", "timezone", "currency", "email", "phone"],
        as_dict=True,
    )
    if not biz:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    mem = frappe.db.get_value(
        "User Business Membership",
        {"user": frappe.session.user, "business_id": biz.business_id, "tenant_id": biz.tenant_id, "active": 1},
        "name",
    )
    if not mem:
        frappe.throw("You do not have access to this business.", frappe.PermissionError)
    return biz


@frappe.whitelist()
def get_business_profile():
    biz = _require_business()
    return {"business": biz}


@frappe.whitelist()
def update_business_profile(business_name: str | None = None, email: str | None = None, phone: str | None = None, industry: str | None = None, location: str | None = None, timezone: str | None = None, currency: str | None = None, **_kw):
    biz = _require_business()
    # Only owners/admins can edit
    role = frappe.db.get_value("User Business Membership", {"user": frappe.session.user, "business_id": biz.business_id, "tenant_id": biz.tenant_id, "active": 1}, "role")
    if role not in ("Owner", "Administrator") and frappe.session.user != "Administrator":
        frappe.throw("Only Owners or Administrators can update business profile.", frappe.PermissionError)

    doc = frappe.get_doc("Business Account", biz.name)
    if business_name is not None and str(business_name).strip():
        doc.business_name = str(business_name).strip()[:140]
    if email is not None:
        email = str(email).strip().lower()
        if email:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                frappe.throw("Invalid email.")
            doc.email = email
        else:
            doc.email = None
    if phone is not None:
        phone = str(phone).strip()[:30]
        doc.phone = phone or None
    if industry is not None:
        doc.industry = str(industry).strip()[:100] or None
    if location is not None:
        doc.location = str(location).strip()[:100] or None
    if timezone is not None and str(timezone).strip():
        tz = str(timezone).strip()
        if tz not in SUPPORTED_TIMEZONES:
            frappe.throw(f"Unsupported timezone. Choose one of: {', '.join(sorted(SUPPORTED_TIMEZONES))}")
        doc.timezone = tz
    if currency is not None and str(currency).strip():
        cur = str(currency).strip().upper()
        if cur not in SUPPORTED_CURRENCIES:
            frappe.throw(f"Unsupported currency. Choose one of: {', '.join(sorted(SUPPORTED_CURRENCIES))}")
        doc.currency = cur

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    fresh = frappe.db.get_value(
        "Business Account",
        biz.name,
        ["name", "business_id", "business_name", "tenant_id", "domain", "status", "industry", "location", "timezone", "currency", "email", "phone"],
        as_dict=True,
    )
    return {"business": fresh}
