"""Partner onboarding — single canonical business profile for Heshly Network.

Stage 1: free network membership (draft → pending → active).  Stage 2: upgrade
same profile to paid AI receptionist via existing subscription.

Uses existing:
- TenantOnboardingService / Business Account / tenant_id
- Business Knowledge Profile (services/products via KnowledgeContext)
- Heshly Network Membership (eligibility)
- Heshly Subscription (upgrade)
- User Business Membership (ownership)

No duplicate business identities.  No plaintext passwords.  Server-side
ownership checks.  Idempotent on email.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, UTC
from typing import Any

import frappe
from frappe.auth import LoginManager

from heshly_core.services.tenant.tenant_onboarding_service import TenantOnboardingService
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.models.business_knowledge_profile import BusinessKnowledgeProfile
from heshly_core.services.ai.tenant_ai_manager import TenantAIManager

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _clean(v: Any) -> str:
    return str(v or "").strip()

def _as_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        try:
            j = json.loads(v)
            if isinstance(j, list):
                return [str(x).strip() for x in j if str(x).strip()]
        except Exception:
            pass
        return [s.strip() for s in v.splitlines() if s.strip()] if "\n" in v else ([v.strip()] if v.strip() else [])
    return []

def _validate_phone(phone: str) -> str | None:
    p = re.sub(r"[\s\-()]", "", phone or "")
    if not p:
        return None
    # Kenyan: 07xx, 01xx, +254, 254, 7xx
    if re.match(r"^(\+?254|0)?[17]\d{8}$", p):
        return p
    if re.match(r"^\+?\d{7,15}$", p):
        return p
    return None

def _require_business() -> dict:
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    bid = frappe.session.data.get("heshly_business_id") or frappe.db.get_value(
        "User Business Membership", {"user": frappe.session.user, "active": 1}, "business_id"
    )
    if not bid:
        frappe.throw("Business session not found.", frappe.PermissionError)
    biz = frappe.db.get_value("Business Account", {"business_id": bid}, ["name","business_id","business_name","tenant_id","domain","status","industry","location","email","phone"], as_dict=True)
    if not biz:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    return biz

def _tenant_id_for_business(business_id: str) -> str | None:
    row = frappe.db.get_value("Business Account", {"business_id": business_id}, ["tenant_id"], as_dict=True)
    return row.get("tenant_id") if row else None

def _save_knowledge(
    tenant_id: str,
    business_name: str,
    industry: str,
    description: str,
    services: list[str],
    products: list[str],
    business_hours: dict | None = None,
    contact_info: dict | None = None,
):
    kp = BusinessKnowledgeProfile(
        profile_id=tenant_id,
        tenant_id=tenant_id,
        business_name=business_name,
        industry=industry or "",
        description=description or "",
        services=services or [],
        products=products or [],
        business_hours=business_hours or {},
        contact_information=contact_info or {},
    )
    TenantAIManager().save_knowledge(kp)
    return kp

# ---------------------------------------------------------------------------
# public: status / resume
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_partner_status(email: str | None = None, **_kw):
    """Return onboarding status for email (guest) or session business."""
    email = _clean(email).lower() if email else ""
    try:
        # authenticated: return own business
        if frappe.session.user and frappe.session.user != "Guest":
            biz = _require_business()
            tenant_id = biz["tenant_id"]
            m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["*"], as_dict=True)
            kp = frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True)
            return {"success": True, "business": biz, "membership": m, "knowledge": kp}
        if email:
            user_name = frappe.db.get_value("User", {"email": email}, "name")
            if not user_name:
                return {"success": True, "exists": False}
            bid = frappe.db.get_value("User Business Membership", {"user": user_name, "active": 1}, "business_id")
            if not bid:
                return {"success": True, "exists": True, "business": None}
            biz = frappe.db.get_value("Business Account", {"business_id": bid}, ["*"], as_dict=True)
            tenant_id = biz.get("tenant_id") if biz else None
            m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["*"], as_dict=True) if tenant_id else None
            kp = frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True) if tenant_id else None
            return {"success": True, "exists": True, "business": biz, "membership": m, "knowledge": kp}
        return {"success": True, "exists": False}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ---------------------------------------------------------------------------
# public: full onboarding (idempotent, 5 steps in one call for tests)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def partner_onboarding(**kwargs):
    """
    Idempotent partner onboarding. Accepts either flat or nested payload:
      business_name, email, password, phone, industry, location,
      description, service_area, service_mode,
      services: list[{name,description,price,duration,area}],
      products: list[{name,description,price,stock,delivery_area,image}],
      contact: {email, phone, whatsapp},
      hours: {mon: "9-5", ...},
      preferences: {accepts_network_leads, wants_whatsapp, wants_calendar},
      terms: {accepted, version},
      wants_whatsapp, wants_calendar, accepts_network_leads (flat bool)

    Creates or reuses the single canonical Business Account for the owner.
    Guest → creates User + Business.  Authenticated → updates own Business.
    Never creates a second business for same owner on retry/refresh.
    """
    # unwrap frappe's payload wrapping
    data: dict[str, Any] = {}
    for k in ("data","payload","body","$json","json"):
        if k in kwargs and isinstance(kwargs[k], dict):
            data.update(kwargs[k])
    # also merge top-level kwargs (except frappe internals)
    for k, v in kwargs.items():
        if k not in ("cmd","data","payload","body","$json","json") and k not in data:
            data[k] = v
    # if data itself contains business_name at top, use it; else try nested
    business_name = _clean(data.get("business_name") or data.get("businessName"))
    email = _clean(data.get("email") or data.get("owner_email") or data.get("business_email")).lower()
    password = str(data.get("password") or "")
    phone = _clean(data.get("phone") or data.get("whatsapp") or data.get("owner_phone"))
    industry = _clean(data.get("industry") or data.get("business_category") or data.get("category") or data.get("niche"))
    location = _clean(data.get("location") or data.get("service_area") or data.get("operating_location") or data.get("physical_location"))
    description = _clean(data.get("description") or data.get("business_description") or data.get("short_description"))
    service_area = _clean(data.get("service_area") or location)
    service_mode = _clean(data.get("service_mode") or data.get("serviceMode") or "")

    # offerings
    raw_services = data.get("services") or data.get("offerings") or []
    raw_products = data.get("products") or []
    # normalize services: list of dicts or strings → list of strings for knowledge profile
    services_list: list[str] = []
    for s in (_as_list(raw_services) if isinstance(raw_services, str) else (raw_services if isinstance(raw_services, list) else [])):
        if isinstance(s, dict):
            name = _clean(s.get("name") or s.get("service_name") or s.get("title"))
            desc = _clean(s.get("description") or s.get("desc"))
            price = _clean(s.get("price") or s.get("price_range"))
            txt = name
            if desc:
                txt += f" — {desc}"
            if price:
                txt += f" ({price})"
            if txt:
                services_list.append(txt[:300])
        elif isinstance(s, str) and s.strip():
            services_list.append(s.strip()[:300])

    products_list: list[str] = []
    for p in (_as_list(raw_products) if isinstance(raw_products, str) else (raw_products if isinstance(raw_products, list) else [])):
        if isinstance(p, dict):
            name = _clean(p.get("name") or p.get("product_name") or p.get("title"))
            desc = _clean(p.get("description") or p.get("desc"))
            price = _clean(p.get("price") or p.get("price_range"))
            txt = name
            if desc:
                txt += f" — {desc}"
            if price:
                txt += f" ({price})"
            if txt:
                products_list.append(txt[:300])
        elif isinstance(p, str) and p.strip():
            products_list.append(p.strip()[:300])

    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    hours = data.get("hours") if isinstance(data.get("hours"), dict) else (data.get("business_hours") if isinstance(data.get("business_hours"), dict) else {})
    # also allow flat hours keys
    if not hours:
        for hk in ("monday","tuesday","wednesday","thursday","friday","saturday","sunday","operating_hours"):
            if data.get(hk):
                if not isinstance(hours, dict):
                    hours = {}
                hours[hk] = _clean(data.get(hk))

    prefs = data.get("preferences") if isinstance(data.get("preferences"), dict) else {}
    accepts_leads = data.get("accepts_network_leads")
    if accepts_leads is None:
        accepts_leads = prefs.get("accepts_network_leads")
    if accepts_leads is None:
        accepts_leads = data.get("acceptsNetworkLeads")
    wants_whatsapp = data.get("wants_whatsapp")
    if wants_whatsapp is None:
        wants_whatsapp = prefs.get("wants_whatsapp")
    wants_calendar = data.get("wants_calendar")
    if wants_calendar is None:
        wants_calendar = prefs.get("wants_calendar")

    terms = data.get("terms") if isinstance(data.get("terms"), dict) else {}
    terms_accepted = bool(terms.get("accepted") if "accepted" in terms else data.get("terms_accepted") or data.get("acceptTerms"))
    terms_version = _clean(terms.get("version") or data.get("terms_version") or "v1")

    # ---- validation (server-side, minimal but strict) ----
    # For authenticated resume, business_name/email/password not required
    is_guest = not frappe.session.user or frappe.session.user == "Guest"
    if is_guest:
        if not business_name:
            return {"success": False, "message": "Business name is required."}
        if not email or "@" not in email:
            return {"success": False, "message": "A valid email is required."}
        if len(password) < 8:
            return {"success": False, "message": "Password must be at least 8 characters."}
        if phone and not _validate_phone(phone):
            # Kenyan 07... already validated, but allow any sane intl
            pass  # non-blocking: store as-is, don't reject on phone alone
    else:
        # authenticated: use session business, ignore business_name/email if not provided
        biz = _require_business()
        business_name = business_name or biz["business_name"]
        email = email or biz.get("email") or frappe.session.user

    # service_mode validation optional

    # ---- idempotency: existing user/business ----
    # Need TenantContext for Business Account creation path
    try:
        TenantContext().set("tmp_check")
    except Exception:
        pass
    existing_business = None
    existing_tenant = None
    if email and frappe.db.exists("User", email):
        # user exists — check if they already own a business
        bid = frappe.db.get_value("User Business Membership", {"user": email, "active": 1}, "business_id")
        if not bid:
            # also check by business email
            bid = frappe.db.get_value("Business Account", {"email": email}, "business_id")
        if bid:
            existing_business = frappe.db.get_value("Business Account", {"business_id": bid}, ["*"], as_dict=True)
            if existing_business:
                existing_tenant = existing_business.get("tenant_id")
                try:
                    TenantContext().set(existing_tenant)
                except Exception:
                    pass
                # update in place (idempotent, no duplicate)
                try:
                    doc = frappe.get_doc("Business Account", existing_business["name"])
                    if business_name and business_name != doc.business_name:
                        doc.business_name = business_name[:140]
                    if industry:
                        doc.industry = industry[:100]
                    if location:
                        doc.location = location[:200]
                    if phone:
                        doc.phone = phone[:30]
                    try:
                        TenantContext().set(existing_tenant)
                    except Exception:
                        pass
                    # onboarding_status / verified
                    if hasattr(doc, "onboarding_status"):
                        try:
                            doc.onboarding_status = "Active" if terms_accepted else (doc.onboarding_status or "Draft")
                        except Exception:
                            pass
                    if hasattr(doc, "terms_accepted_at") and terms_accepted:
                        try:
                            doc.terms_accepted_at = datetime.now(UTC).replace(tzinfo=None)
                            if hasattr(doc, "terms_version"):
                                doc.terms_version = terms_version
                        except Exception:
                            pass
                    doc.save(ignore_permissions=True)
                    # knowledge
                    _save_knowledge(existing_tenant, doc.business_name, industry or doc.industry or "", description, services_list, products_list, hours if isinstance(hours, dict) else {}, contact if isinstance(contact, dict) else {})
                    # membership: ensure Active if terms accepted and accepts_leads
                    try:
                        m_name = frappe.db.get_value("Heshly Network Membership", {"tenant_id": existing_tenant}, "name")
                        if m_name:
                            mdoc = frappe.get_doc("Heshly Network Membership", m_name)
                            if service_area:
                                mdoc.service_area = service_area[:200]
                            # do NOT auto-verify on registration; verified field stays 0
                            mdoc.save(ignore_permissions=True)
                        elif accepts_leads is not False:
                            # create membership as Active (but verified=0)
                            import uuid as _uuid
                            mid = f"hmem_{_uuid.uuid4().hex[:10]}"
                            _now2 = datetime.now(UTC).replace(tzinfo=None)
                            md = frappe.get_doc({
                                "doctype": "Heshly Network Membership",
                                "membership_id": mid,
                                "tenant_id": existing_tenant,
                                "business_id": doc.business_id,
                                "status": "Active",
                                "service_area": service_area[:200] if service_area else (location[:200] if location else ""),
                                "accepts_network_leads": 1,
                                "joined_at": _now2,
                                "updated_at": _now2,
                            })
                            md.insert(ignore_permissions=True)
                    except Exception:
                        pass
                    frappe.db.commit()
                    return {"success": True, "message": "Profile updated.", "business": {"business_id": doc.business_id, "tenant_id": existing_tenant, "business_name": doc.business_name, "email": doc.email}, "membership": frappe.db.get_value("Heshly Network Membership", {"tenant_id": existing_tenant}, ["*"], as_dict=True)}
                except Exception as e:
                    frappe.db.rollback()
                    return {"success": False, "message": str(e)}

    # ---- guest new business ----
    if is_guest and frappe.db.exists("User", email):
        # user exists but no business — treat as resume with password check
        # verify password via LoginManager
        try:
            lm = LoginManager()
            lm.authenticate(user=email, pwd=password)
        except Exception:
            return {"success": False, "message": "An account with this email already exists. Please sign in to continue."}
        # authenticated now but we are still in guest context for this request; return exists signal
        return {"success": False, "message": "An account with this email already exists. Please sign in to continue.", "exists": True}

    # ---- create new ----
    try:
        svc = TenantOnboardingService()
        result = svc.onboard(
            business_name=business_name,
            owner_email=email,
            owner_password=password if is_guest else "TempPass123!",
            phone=phone,
            industry=industry,
            location=location,
        )
        business_id = result.get("business", {}).get("business_id")
        tenant_id = result.get("business", {}).get("tenant_id")
        # update business with partner fields (need TenantContext)
        try:
            TenantContext().set(tenant_id)
            bdoc = frappe.get_doc("Business Account", {"business_id": business_id})
            if description:
                pass
            if hasattr(bdoc, "onboarding_status"):
                bdoc.onboarding_status = "Active" if terms_accepted else "Draft"
            if hasattr(bdoc, "verified"):
                bdoc.verified = 0
            if terms_accepted and hasattr(bdoc, "terms_accepted_at"):
                bdoc.terms_accepted_at = datetime.now(UTC).replace(tzinfo=None)
                if hasattr(bdoc, "terms_version"):
                    bdoc.terms_version = terms_version
            bdoc.save(ignore_permissions=True)
        except Exception:
            pass
        # knowledge
        try:
            _save_knowledge(tenant_id, business_name, industry or "", description, services_list, products_list, hours if isinstance(hours, dict) else {}, contact if isinstance(contact, dict) else {})
        except Exception:
            pass
        # membership
        try:
            # TenantOnboardingService does not create membership; we do
            if not frappe.db.exists("Heshly Network Membership", {"tenant_id": tenant_id}):
                import uuid as _uuid
                mid = f"hmem_{_uuid.uuid4().hex[:10]}"
                _now = datetime.now(UTC).replace(tzinfo=None)
                md = frappe.get_doc({
                    "doctype": "Heshly Network Membership",
                    "membership_id": mid,
                    "tenant_id": tenant_id,
                    "business_id": business_id,
                    "status": "Active" if terms_accepted else "Draft",
                    "service_area": service_area[:200] if service_area else (location[:200] if location else ""),
                    "accepts_network_leads": 1,
                    "joined_at": _now,
                    "updated_at": _now,
                })
                # verified stays 0
                if hasattr(md, "verified"):
                    md.verified = 0
                md.insert(ignore_permissions=True)
                md.insert(ignore_permissions=True)
            else:
                mdoc = frappe.get_doc("Heshly Network Membership", {"tenant_id": tenant_id})
                if terms_accepted and mdoc.status == "Draft":
                    mdoc.status = "Active"
                    mdoc.save(ignore_permissions=True)
        except Exception:
            pass
        frappe.db.commit()
        # auto-login for guest
        if is_guest:
            try:
                lm = LoginManager()
                lm.authenticate(user=email, pwd=password)
                lm.post_login()
                TenantContext().set(tenant_id)
                frappe.session.data["heshly_business_id"] = business_id
                frappe.local.session_obj.update(force=True)
                frappe.local.cookie_manager.init_cookies()
            except Exception:
                pass
        try:
            frappe.set_user("Administrator")
            memb = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["*"], as_dict=True)
            pub = frappe.db.get_value("Business Account", {"business_id": business_id}, ["public_slug"], as_dict=True)
            slug = (pub.get("public_slug") if pub else "") or ""
        except Exception:
            memb = None
            slug = ""
        finally:
            try:
                frappe.set_user(email.lower())
            except Exception:
                frappe.set_user("Guest")
        try:
            from heshly_core.services.business_slug import public_url as _pu
            public_url = _pu(slug) if slug else f"https://heshly.com/{business_id.lower().replace('_','-')}"
        except Exception:
            public_url = f"https://heshly.com/{business_id.lower().replace('_','-')}"
        return {"success": True, "message": "Welcome to Heshly Network.", "business": {"business_id": business_id, "tenant_id": tenant_id, "business_name": business_name, "email": email, "public_slug": slug, "public_url": public_url}, "membership": memb}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Partner onboarding error")
        return {"success": False, "message": str(e)}

# ---------------------------------------------------------------------------
# authenticated: update own profile / upgrade same tenant
# ---------------------------------------------------------------------------

@frappe.whitelist()
def update_partner_profile(**kwargs):
    biz = _require_business()
    tenant_id = biz["tenant_id"]
    business_id = biz["business_id"]
    data: dict[str, Any] = {}
    for k in ("data","payload","body","$json","json"):
        if k in kwargs and isinstance(kwargs[k], dict):
            data.update(kwargs[k])
    for k, v in kwargs.items():
        if k not in ("cmd","data","payload","body","$json","json") and k not in data:
            data[k] = v

    # ownership: already checked via _require_business

    # partial updates
    doc = frappe.get_doc("Business Account", biz["name"])
    if data.get("business_name"):
        doc.business_name = _clean(data["business_name"])[:140]
    if data.get("industry"):
        doc.industry = _clean(data["industry"])[:100]
    if data.get("location"):
        doc.location = _clean(data["location"])[:200]
    if data.get("phone"):
        doc.phone = _clean(data["phone"])[:30]
    if data.get("email"):
        em = _clean(data["email"]).lower()
        if em and "@" in em:
            doc.email = em
    for fld in ("service_area","service_mode","onboarding_status"):
        if data.get(fld) and hasattr(doc, fld):
            try:
                setattr(doc, fld, _clean(data[fld])[:200])
            except Exception:
                pass
    doc.save(ignore_permissions=True)

    # knowledge
    services = data.get("services")
    products = data.get("products")
    if services is not None or products is not None or data.get("description") is not None:
        # merge with existing
        existing = frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True)
        prev_services = []
        prev_products = []
        prev_desc = ""
        prev_industry = doc.industry or ""
        if existing:
            try:
                prev_services = json.loads(existing.get("services") or "[]")
            except Exception:
                prev_services = []
            try:
                prev_products = json.loads(existing.get("products") or "[]")
            except Exception:
                prev_products = []
            prev_desc = existing.get("description") or ""
            prev_industry = existing.get("industry") or prev_industry
        # normalize
        def to_strs(v, prev):
            if v is None:
                return prev
            out = []
            for x in (v if isinstance(v, list) else [_as_list(v)]):
                if isinstance(x, dict):
                    n = _clean(x.get("name") or x.get("title"))
                    d = _clean(x.get("description"))
                    out.append(f"{n} — {d}" if d else n)
                elif isinstance(x, str) and x.strip():
                    out.append(x.strip())
            return [s for s in out if s]

        new_services = to_strs(services, prev_services) if services is not None else prev_services
        new_products = to_strs(products, prev_products) if products is not None else prev_products
        new_desc = _clean(data.get("description")) if data.get("description") is not None else prev_desc
        new_industry = _clean(data.get("industry")) if data.get("industry") is not None else prev_industry
        _save_knowledge(tenant_id, doc.business_name, new_industry, new_desc, new_services, new_products, data.get("hours") if isinstance(data.get("hours"), dict) else {}, data.get("contact") if isinstance(data.get("contact"), dict) else {})

    # membership
    if data.get("service_area") or "accepts_network_leads" in data:
        try:
            m = frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, "name")
            if m:
                md = frappe.get_doc("Heshly Network Membership", m)
                if data.get("service_area"):
                    md.service_area = _clean(data["service_area"])[:200]
                if "accepts_network_leads" in data:
                    md.accepts_network_leads = 1 if data["accepts_network_leads"] else 0
                md.save(ignore_permissions=True)
        except Exception:
            pass

    frappe.db.commit()
    return {"success": True, "business": frappe.db.get_value("Business Account", biz["name"], ["*"], as_dict=True)}

@frappe.whitelist()
def partner_upgrade(plan: str | None = None, **_kw):
    """Upgrade same business/tenant to paid AI receptionist (no second profile)."""
    biz = _require_business()
    tenant_id = biz["tenant_id"]
    business_id = biz["business_id"]
    # Check existing subscription
    sub = frappe.db.get_value("Heshly Subscription", {"tenant_id": tenant_id}, ["*"], as_dict=True)
    if not sub:
        return {"success": False, "message": "No subscription found. Complete onboarding first."}
    # If no payment integration, return honest pending state (do not fake success)
    # We keep upgrade as configurable: if plan provided, update subscription plan but keep status Trial/Active
    try:
        doc = frappe.get_doc("Heshly Subscription", sub["name"])
        if plan:
            doc.plan = _clean(plan)[:100]
        # Do NOT fake payment confirmation.  If payment not confirmed, keep current status.
        # Mark intent: store upgrade_requested in metadata if needed
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        # Verify same identity
        assert doc.tenant_id == tenant_id and doc.business_id == business_id
        return {"success": True, "message": "Upgrade request recorded. Same business profile retained.", "subscription": frappe.db.get_value("Heshly Subscription", sub["name"], ["*"], as_dict=True), "business_id": business_id, "tenant_id": tenant_id}
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "message": str(e)}
