from __future__ import annotations

import frappe
from frappe.auth import LoginManager

from heshly_core.services.tenant.tenant_onboarding_service import (
    TenantOnboardingService,
)
from heshly_core.services.tenant.tenant_context import TenantContext


@frappe.whitelist(allow_guest=True)
def signup(
    business_name: str,
    email: str,
    password: str,
    phone: str | None = None,
    industry: str | None = None,
    location: str | None = None,
):
    """
    Public Heshly signup endpoint.

    Creates:
        Business Account
        14-day Trial Subscription
        Owner User
        Owner Membership

    This endpoint is intentionally public.

    CSRF protection is disabled only for this
    public signup endpoint. Authentication,
    authenticated business APIs, and the rest
    of ERPNext remain protected.
    """

    business_name = (business_name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not business_name:
        frappe.throw(
            "Business name is required.",
            frappe.ValidationError,
        )

    if not email or "@" not in email:
        frappe.throw(
            "A valid email address is required.",
            frappe.ValidationError,
        )

    if len(password) < 8:
        frappe.throw(
            "Password must be at least 8 characters.",
            frappe.ValidationError,
        )

    try:
        service = TenantOnboardingService()

        result = service.onboard(
            business_name=business_name,
            owner_email=email,
            owner_password=password,
            phone=phone,
            industry=industry,
            location=location,
        )

        # Auto-login the newly created owner so the signup→redirect
        # lands authenticated (same mechanism as login_business).
        # Uses LoginManager to create session + sid cookie; bound to
        # the new tenant/business for get_current_business.
        try:
            business_id = result.get("business", {}).get("business_id") if isinstance(result, dict) else None  # type: ignore
            tenant_id = result.get("business", {}).get("tenant_id") if isinstance(result, dict) else None  # type: ignore
            if business_id and tenant_id and isinstance(email, str) and email:
                # Canonical user name
                _user = email.strip().lower()
                _canonical = frappe.db.get_value("User", {"email": _user}, "name") or _user  # type: ignore
                lm = LoginManager()
                lm.authenticate(user=_canonical, pwd=password)
                lm.post_login()
                # Reassert tenant context after LoginManager (may clear thread-locals)
                try:
                    TenantContext().set(tenant_id)
                except Exception:
                    pass
                frappe.session.data["heshly_business_id"] = business_id  # type: ignore
                frappe.local.session_obj.update(force=True)  # type: ignore
                frappe.local.cookie_manager.init_cookies()  # type: ignore
                # Ensure heshly_business_id available in response for redirect
                # (already in result)
        except Exception:
            # Signup still succeeded — don't fail the request if auto-login races.
            # Frontend will fall back to explicit login on tenant domain.
            frappe.log_error(frappe.get_traceback(), "Signup auto-login failed")  # type: ignore

        return result

    except ValueError as exc:
        frappe.throw(
            str(exc),
            frappe.ValidationError,
        )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Heshly Signup Error",
        )

        frappe.throw(
            "Unable to create your Heshly account. "
            "Please try again.",
            frappe.ValidationError,
        )
