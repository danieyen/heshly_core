from __future__ import annotations

import re

import frappe

from heshly_core.services.tenant.tenant_context import TenantContext

ROLES = {"Owner", "Administrator", "Member", "Viewer"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _require_business():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    bid = frappe.session.data.get("heshly_business_id")
    if not bid:
        frappe.throw("Business session not found.", frappe.PermissionError)
    biz = frappe.db.get_value(
        "Business Account",
        {"business_id": bid, "status": "Active"},
        ["business_id", "business_name", "tenant_id", "domain", "status"],
        as_dict=True,
    )
    if not biz:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    mem = frappe.db.get_value(
        "User Business Membership",
        {"user": frappe.session.user, "business_id": biz.business_id, "tenant_id": biz.tenant_id, "active": 1},
        ["role", "name"],
        as_dict=True,
    )
    if not mem:
        frappe.throw("You do not have access to this business.", frappe.PermissionError)
    return biz, mem


def _can_manage(biz, mem) -> bool:
    return (mem.role or "").strip() in ("Owner", "Administrator") or frappe.session.user == "Administrator"


def _user_display(user: str):
    u = frappe.db.get_value("User", user, ["email", "full_name", "enabled"], as_dict=True)
    if not u:
        return {"user": user, "email": user, "name": user, "enabled": 0}
    return {
        "user": user,
        "email": u.email or user,
        "name": (u.full_name or user).strip(),
        "enabled": int(u.enabled or 0),
    }


@frappe.whitelist()
def list_members():
    biz, _mem = _require_business()
    rows = frappe.get_all(
        "User Business Membership",
        filters={"business_id": biz.business_id, "tenant_id": biz.tenant_id},
        fields=["name", "user", "business_id", "tenant_id", "role", "active", "invited_by", "creation", "modified"],
        order_by="creation asc",
    )
    # Enrich with User
    for r in rows:
        disp = _user_display(r.user)
        r["email"] = disp["email"]
        r["name_display"] = disp["name"]
        r["user_enabled"] = disp["enabled"]
    return rows


@frappe.whitelist()
def invite_member(email: str | None = None, role: str | None = None, full_name: str | None = None):
    biz, mem = _require_business()
    if not _can_manage(biz, mem):
        frappe.throw("Only Owners and Administrators can invite members.", frappe.PermissionError)
    email = (email or "").strip().lower()
    if not email or not EMAIL_RE.match(email):
        frappe.throw("A valid email is required.")
    role = (role or "Member").strip()
    if role not in ROLES:
        frappe.throw(f"Invalid role. Choose one of: {', '.join(sorted(ROLES))}")
    full_name = (full_name or "").strip()
    # Check existing membership
    existing = frappe.db.get_value(
        "User Business Membership",
        {"user": ["in", [email, email.lower()]], "business_id": biz.business_id, "tenant_id": biz.tenant_id},
        "name",
    )
    # Also check by email case-insensitive via User lookup
    if not existing:
        user_name = frappe.db.get_value("User", {"email": email}, "name")
        if user_name:
            existing = frappe.db.get_value(
                "User Business Membership",
                {"user": user_name, "business_id": biz.business_id, "tenant_id": biz.tenant_id},
                "name",
            )
            if existing:
                frappe.throw("This person is already a member of this business.")
        # Check that duplicate Membership with that email string as user won't leak
        dup = frappe.db.get_all(
            "User Business Membership",
            filters={"business_id": biz.business_id, "tenant_id": biz.tenant_id},
            fields=["user"],
        )
        for d in dup:
            if (d.user or "").strip().lower() == email:
                frappe.throw("This person is already a member of this business.")

    # Create or reuse User
    user_name = frappe.db.get_value("User", {"email": email}, "name")
    if not user_name:
        # Use Frappe's user creation (Website User)
        from frappe.utils import random_string

        user_doc = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": (full_name.split()[0] if full_name else email.split("@")[0]),
                "last_name": " ".join(full_name.split()[1:]) if full_name and " " in full_name else "",
                "enabled": 1,
                "new_password": random_string(12),
                "user_type": "Website User",
                "send_welcome_email": 0,
            }
        )
        user_doc.flags.ignore_permissions = True
        user_doc.insert(ignore_permissions=True)
        user_name = user_doc.name
        # Send reset link for invitee to set password
        try:
            from frappe.utils import now_datetime

            # Generate reset key via standard method
            user_doc = frappe.get_doc("User", user_name)
            user_doc.flags.ignore_permissions = True
            # Use built-in password reset flow
            from frappe.core.doctype.user.user import generate_keys

            generate_keys(user_name)
        except Exception:
            pass
    else:
        # Ensure enabled
        try:
            frappe.db.set_value("User", user_name, "enabled", 1)
        except Exception:
            pass

    # Create membership
    m = frappe.new_doc("User Business Membership")
    m.membership_id = frappe.generate_hash(length=12)
    m.user = user_name
    m.tenant_id = biz.tenant_id
    m.business_id = biz.business_id
    m.role = role
    m.active = 1
    m.invited_by = frappe.session.user
    m.flags.ignore_permissions = True
    m.insert(ignore_permissions=True)
    frappe.db.commit()

    disp = _user_display(user_name)
    return {
        "membership": m.name,
        "user": user_name,
        "email": disp["email"],
        "name": disp["name"],
        "role": role,
        "active": 1,
    }


@frappe.whitelist()
def update_member_role(user: str | None = None, role: str | None = None):
    biz, mem = _require_business()
    if not _can_manage(biz, mem):
        frappe.throw("Only Owners and Administrators can change roles.", frappe.PermissionError)
    user = (user or "").strip()
    role = (role or "").strip()
    if not user:
        frappe.throw("user is required.")
    if role not in ROLES:
        frappe.throw(f"Invalid role. Choose one of: {', '.join(sorted(ROLES))}")
    # Prevent self-demotion if last owner?
    row = frappe.db.get_value(
        "User Business Membership",
        {"user": user, "business_id": biz.business_id, "tenant_id": biz.tenant_id},
        ["name", "role"],
        as_dict=True,
    )
    if not row:
        frappe.throw("Membership not found.")
    frappe.db.set_value("User Business Membership", row.name, "role", role)
    frappe.db.commit()
    return {"user": user, "role": role}


@frappe.whitelist()
def remove_member(user: str | None = None):
    biz, mem = _require_business()
    if not _can_manage(biz, mem):
        frappe.throw("Only Owners and Administrators can remove members.", frappe.PermissionError)
    user = (user or "").strip()
    if not user:
        frappe.throw("user is required.")
    if user == frappe.session.user:
        frappe.throw("You cannot remove yourself.")
    row = frappe.db.get_value(
        "User Business Membership",
        {"user": user, "business_id": biz.business_id, "tenant_id": biz.tenant_id},
        "name",
        as_dict=True,
    )
    if not row:
        frappe.throw("Membership not found.")
    frappe.delete_doc("User Business Membership", row.name, ignore_permissions=True)
    frappe.db.commit()
    return {"removed": user}


@frappe.whitelist()
def resend_invite(user: str | None = None):
    biz, mem = _require_business()
    if not _can_manage(biz, mem):
        frappe.throw("Only Owners and Administrators can resend invitations.", frappe.PermissionError)
    user = (user or "").strip()
    if not user:
        frappe.throw("user is required.")
    # Reset password key so user can set password via /update-password?key=...
    try:
        from frappe.core.doctype.user.user import reset_password

        # Use built-in: generate reset key and email
        doc = frappe.get_doc("User", user)
        doc.flags.ignore_permissions = True
        doc.reset_password(send_email=True)
    except Exception as e:
        frappe.throw(str(e))
    return {"user": user, "resent": True}
