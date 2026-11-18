"""Admin Business Management — System Manager only.

Reuses: Business Account, Business Knowledge Profile, Heshly Network Membership,
TenantOnboardingService, TenantAIManager/BusinessConfigurationRepository.

No new Service DocType, no Appointment catalogue.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, UTC
from typing import Any

import frappe

from heshly_core.services.tenant.tenant_onboarding_service import TenantOnboardingService
from heshly_core.services.tenant.tenant_id_strategy import TenantIDStrategy
from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.ai.tenant_ai_manager import TenantAIManager
from heshly_core.models.business_knowledge_profile import BusinessKnowledgeProfile

ALLOWED_CURRENCIES = {"KES","USD","EUR","GBP","AED","ZAR","INR","SGD"}

def _require_system_manager():
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    roles = frappe.get_roles(frappe.session.user) or []
    if "System Manager" not in roles and "Administrator" not in roles:
        frappe.throw("Not permitted", frappe.PermissionError)

def _clean(s: Any) -> str:
    return str(s or "").strip()

def _as_services(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out=[]
        for x in v:
            if isinstance(x, dict):
                n=_clean(x.get("name") or x.get("service_name") or x.get("title"))
                if n: out.append(n[:300])
            elif isinstance(x, str) and x.strip():
                out.append(x.strip()[:300])
        return [s for s in out if s]
    if isinstance(v, str):
        v=v.strip()
        if not v: return []
        try:
            j=json.loads(v)
            if isinstance(j, list):
                return _as_services(j)
        except: pass
        # newline or comma separated
        parts=re.split(r"[\n,]+", v)
        return [p.strip()[:300] for p in parts if p.strip()]
    return []

def _validate_email(s: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s))

def _validate_phone(s: str) -> bool:
    if not s: return True
    p=re.sub(r"[\s\-()]", "", s)
    return bool(re.match(r"^(\+?254|0)?[17]\d{8}$", p) or re.match(r"^\+?\d{7,15}$", p))

def _save_knowledge(tenant_id: str, business_name: str, industry: str, description: str, services: list[str]):
    # Preserve existing products/faqs/policies; only update services/description
    existing = frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True)
    prev_desc = (existing or {}).get("description") or ""
    prev_industry = (existing or {}).get("industry") or industry
    prev_services=[]
    if existing and existing.get("services"):
        try:
            v=json.loads(existing["services"])
            if isinstance(v, list): prev_services=v
        except: pass
    # If services explicitly provided (including empty), use it; else keep prev
    # Caller decides — here we always set to provided services
    final_desc = description if description is not None else prev_desc
    kp = BusinessKnowledgeProfile(
        profile_id=tenant_id,
        tenant_id=tenant_id,
        business_name=business_name,
        industry=industry or prev_industry or "",
        description=final_desc or "",
        services=services or [],
    )
    # Keep products/faqs/policies from existing
    if existing:
        try:
            kp.products=json.loads(existing.get("products") or "[]") if isinstance(existing.get("products"), str) else (existing.get("products") or [])
        except: kp.products=[]
        try:
            kp.faqs=json.loads(existing.get("faqs") or "[]") if isinstance(existing.get("faqs"), str) else (existing.get("faqs") or [])
        except: kp.faqs=[]
        try:
            kp.policies=json.loads(existing.get("policies") or "[]") if isinstance(existing.get("policies"), str) else (existing.get("policies") or [])
        except: kp.policies=[]
    TenantAIManager().save_knowledge(kp)
    return kp

def _serialize_business(biz_row: dict, membership_row: dict | None = None, knowledge_row: dict | None = None) -> dict:
    services=[]
    if knowledge_row and knowledge_row.get("services"):
        try:
            v=json.loads(knowledge_row["services"])
            if isinstance(v, list): services=v
        except: services=[]
    is_test = (biz_row.get("tenant_id") or "").lower().startswith("test_") or (biz_row.get("business_id") or "").lower().startswith("test_")
    # Also check tenant with hcn_e2e/net_test
    tid=(biz_row.get("tenant_id") or "").lower()
    if tid.startswith("hcn_e2e_") or tid.startswith("net_test_") or "e2e" in tid:
        is_test=True
    return {
        "name": biz_row.get("name"),
        "business_id": biz_row.get("business_id"),
        "business_name": biz_row.get("business_name"),
        "tenant_id": biz_row.get("tenant_id"),
        "domain": biz_row.get("domain"),
        "email": biz_row.get("email"),
        "phone": biz_row.get("phone"),
        "status": biz_row.get("status"),
        "industry": biz_row.get("industry"),
        "location": biz_row.get("location"),
        "timezone": biz_row.get("timezone"),
        "currency": biz_row.get("currency"),
        "public_slug": biz_row.get("public_slug"),
        "is_test": is_test,
        "membership": {
            "membership_id": membership_row.get("membership_id") if membership_row else None,
            "status": membership_row.get("status") if membership_row else None,
            "service_area": membership_row.get("service_area") if membership_row else None,
            "accepts_network_leads": membership_row.get("accepts_network_leads") if membership_row else None,
            "verified": membership_row.get("verified") if membership_row and "verified" in membership_row else None,
        } if membership_row is not None else None,
        "services": services,
        "description": (knowledge_row or {}).get("description") or "",
    }

@frappe.whitelist()
def admin_list_businesses(search: str | None = None, status: str | None = None, is_test: str | None = None, limit: int = 50, offset: int = 0, **kw):
    _require_system_manager()
    try: limit=max(1, min(int(limit), 200))
    except: limit=50
    try: offset=max(0, int(offset))
    except: offset=0
    search=_clean(search or kw.get("q") or "")
    status=_clean(status or kw.get("filter_status") or "")
    # Build frappe filters
    filters={}
    if status:
        filters["status"]=status
    # Search via or_filters
    rows=[]
    try:
        if search:
            rows=frappe.get_all("Business Account", filters=filters or None, or_filters=[["business_name","like",f"%{search}%"],["business_id","like",f"%{search}%"],["tenant_id","like",f"%{search}%"],["location","like",f"%{search}%"]], fields=["*"], order_by="modified desc", limit_start=offset, limit_page_length=limit)
        else:
            rows=frappe.get_all("Business Account", filters=filters or None, fields=["*"], order_by="modified desc", limit_start=offset, limit_page_length=limit)
    except Exception as e:
        # Fallback for frappe versions without or_filters
        rows=frappe.get_all("Business Account", filters=filters or None, fields=["*"], order_by="modified desc", limit_start=offset, limit_page_length=limit)
        if search:
            sl=search.lower()
            rows=[r for r in rows if sl in (r.get("business_name") or "").lower() or sl in (r.get("business_id") or "").lower() or sl in (r.get("location") or "").lower()]
    # Attach membership+knowledge
    out=[]
    for r in rows:
        tid=r.get("tenant_id")
        try: m=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tid}, ["*"], as_dict=True) if tid else None
        except: m=None
        try: kp=frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tid}, ["*"], as_dict=True) if tid else None
        except: kp=None
        item=_serialize_business(r, m, kp)
        # client-side filter is_test if requested
        if is_test is not None and _clean(is_test) != "":
            want = _clean(is_test).lower() in ("1","true","yes","test")
            if want and not item["is_test"]: continue
            if not want and item["is_test"]: continue
        out.append(item)
    total = frappe.db.count("Business Account", filters=filters or None) if not search else len(out)+offset if len(out)==limit else len(out)+offset
    # For search, we did client filter, so count is approximate
    return {"success": True, "businesses": out, "total": total, "limit": limit, "offset": offset}

@frappe.whitelist()
def admin_get_business(business_id: str | None = None, name: str | None = None, **kw):
    _require_system_manager()
    bid=_clean(business_id or kw.get("business_id") or name or kw.get("name") or "")
    if not bid:
        frappe.throw("business_id is required")
    row=None
    if frappe.db.exists("Business Account", {"business_id": bid}):
        row=frappe.db.get_value("Business Account", {"business_id": bid}, ["*"], as_dict=True)
    elif frappe.db.exists("Business Account", bid):
        row=frappe.db.get_value("Business Account", bid, ["*"], as_dict=True)
    if not row:
        frappe.throw("Business not found", frappe.DoesNotExistError)
    m=frappe.db.get_value("Heshly Network Membership", {"tenant_id": row.get("tenant_id")}, ["*"], as_dict=True) if row.get("tenant_id") else None
    kp=frappe.db.get_value("Business Knowledge Profile", {"tenant_id": row.get("tenant_id")}, ["*"], as_dict=True) if row.get("tenant_id") else None
    return {"success": True, "business": _serialize_business(row, m, kp)}

@frappe.whitelist()
def admin_create_business(**kwargs):
    _require_system_manager()
    data: dict[str,Any]={}
    for k in ("data","payload","body","$json","json"):
        if k in kwargs and isinstance(kwargs[k], dict):
            data.update(kwargs[k])
    for k,v in kwargs.items():
        if k not in ("cmd","data","payload","body","$json","json") and k not in data:
            data[k]=v
    # also parse JSON strings
    for k in list(data.keys()):
        if isinstance(data[k], str) and data[k].strip().startswith("{"):
            try:
                j=json.loads(data[k])
                if isinstance(j, dict) and k in ("business","payload"): data.update(j)
            except: pass

    business_name=_clean(data.get("business_name") or data.get("name"))
    business_id=_clean(data.get("business_id") or "")
    category=_clean(data.get("category") or data.get("industry"))
    location=_clean(data.get("location"))
    service_area=_clean(data.get("service_area") or data.get("service_areas") or location)
    phone=_clean(data.get("phone"))
    whatsapp=_clean(data.get("whatsapp") or data.get("whatsapp_number") or data.get("whatsappNumber"))
    email=_clean(data.get("email") or "").lower()
    description=_clean(data.get("description"))
    services=_as_services(data.get("services"))
    pricing=_clean(data.get("pricing") or data.get("price_info") or "")
    status_val=_clean(data.get("status") or "Active")
    is_test=bool(data.get("is_test") or data.get("isTest") or data.get("test_business"))
    verified = data.get("verified")  # 0/1 or None
    accepts_leads = data.get("accepts_network_leads")
    if accepts_leads is None: accepts_leads = data.get("acceptsNetworkLeads")
    if accepts_leads is None: accepts_leads = True

    # Validation server-side
    if not business_name:
        return {"success": False, "message": "Business name is required."}
    if email and not _validate_email(email):
        return {"success": False, "message": "Invalid email."}
    if phone and not _validate_phone(phone):
        return {"success": False, "message": "Invalid phone number."}
    if whatsapp and not _validate_phone(whatsapp):
        return {"success": False, "message": "Invalid WhatsApp number."}
    if not location:
        return {"success": False, "message": "Location is required."}
    if not services:
        return {"success": False, "message": "At least one service is required."}
    if len(services) > 30:
        return {"success": False, "message": "Too many services (max 30)."}
    for s in services:
        if not s or len(s) > 200:
            return {"success": False, "message": f"Invalid service: {s[:50]}"}
    if status_val not in ("Active","Inactive","Suspended"):
        status_val="Active"
    # Pricing optional but sanitize
    if pricing and len(pricing) > 2000:
        return {"success": False, "message": "Pricing info too long."}

    # Business ID: generate if not provided
    if not business_id:
        business_id=TenantOnboardingService.make_business_id(business_name, email or f"admin-{uuid.uuid4().hex[:6]}@heshly.com")
    else:
        business_id=re.sub(r"[^a-zA-Z0-9_]+","_", business_id).strip("_")
        if frappe.db.exists("Business Account", {"business_id": business_id}):
            return {"success": False, "message": "Business ID already exists."}
    # Test business prefix: ensure tenant_id reflects test
    if is_test:
        # Ensure business_id/tenant starts with test_ so _is_test_tenant_id filters it
        if not business_id.lower().startswith("test_"):
            business_id = f"test_{business_id}"
        # Re-check uniqueness
        if frappe.db.exists("Business Account", {"business_id": business_id}):
            business_id = f"{business_id}_{uuid.uuid4().hex[:4]}"

    owner_email = email or f"{business_id.lower()}@admin.heshly.local"
    if not frappe.db.exists("User", owner_email):
        # Create a placeholder admin-owned user if needed, but prefer existing admin user
        try:
            owner_email = frappe.session.user if frappe.session.user != "Guest" else owner_email
        except: pass

    # Use TenantOnboardingService for canonical creation (creates Business Account, tenant_id, User, Membership, Subscription)
    # We set TenantContext correctly and reuse existing flows
    try:
        # Generate tenant_id
        tenant_id=TenantIDStrategy.from_business_id(business_id)
        # If test, ensure tenant also test_
        if is_test and not tenant_id.startswith("test_"):
            tenant_id = f"test_{tenant_id}"
        TenantContext().set(tenant_id)
    except Exception as e:
        return {"success": False, "message": str(e)}

    # For test businesses, we want deterministic creation without requiring a new User password flow
    # Create via TenantOnboardingService with a generated temp password, or directly via repo if test
    try:
        # Try onboarding path
        temp_pwd = f"Tmp{uuid.uuid4().hex[:8]}Aa1!"
        svc=TenantOnboardingService()
        # Check if user already exists for this admin email
        onboarding_email = owner_email
        # For admin-created, we don't want to reuse password validation of existing user; create unique business_id already ensures
        # If owner_email exists, onboarding will fail with "already exists" — use a generated owner email for test businesses
        if is_test and frappe.db.exists("User", onboarding_email):
            onboarding_email = f"{business_id.lower()}@test.heshly.local"
        if frappe.db.exists("User", onboarding_email):
            # Use a fresh email for this business
            onboarding_email = f"{business_id.lower()}+{uuid.uuid4().hex[:4]}@heshly.local"
        result=svc.onboard(
            business_name=business_name,
            owner_email=onboarding_email,
            owner_password=temp_pwd,
            phone=phone or whatsapp or None,
            industry=category or "",
            location=location,
        )
        business_id=result.get("business",{}).get("business_id") or business_id
        tenant_id=result.get("business",{}).get("tenant_id") or tenant_id
        TenantContext().set(tenant_id)
        # Update Business Account with admin fields
        # Need tenant context for save
        bdoc=frappe.get_doc("Business Account", {"business_id": business_id})
        if category: bdoc.industry = category[:100]
        if email: bdoc.email = email.lower()[:140]
        if phone: bdoc.phone = phone[:30]
        # Status via BusinessAccount model save will map, but we can set directly
        # Frappe Business Account status select Active/Inactive/Suspended
        try:
            bdoc.status = status_val
        except: pass
        # Also set domain invariant already handled by repo
        bdoc.save(ignore_permissions=True)

        # Knowledge: services via BusinessKnowledgeProfile.services (list[str]) — compatible with KnowledgeContext
        desc_with_pricing = description
        if pricing:
            desc_with_pricing = (description + "\n\nPricing: " + pricing) if description else f"Pricing: {pricing}"
        _save_knowledge(tenant_id, business_name, category or "", desc_with_pricing, services)

        # Membership: ensure service_area, accepts_network_leads, and test business excluded unless explicitly enabled
        # Test businesses: accepts_network_leads should be 0 unless admin explicitly enabled test mode (we keep 0 by default)
        # But we respect accepts_leads param — for test, default to 0 to avoid real leads
        if is_test and accepts_leads is True and data.get("accepts_network_leads") is None:
            # Admin didn't explicitly enable — keep disabled for test
            accepts_leads=False
        m_name=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, "name")
        if m_name:
            mdoc=frappe.get_doc("Heshly Network Membership", m_name)
            if service_area: mdoc.service_area=service_area[:200]
            # For test business, ensure not in production: if is_test and not explicitly enabled, keep 0
            # Otherwise set per param
            try:
                mdoc.accepts_network_leads = 1 if accepts_leads else 0
            except: pass
            if service_area: mdoc.service_area=service_area[:200]
            mdoc.save(ignore_permissions=True)
        else:
            import datetime
            mid=f"hmem_{uuid.uuid4().hex[:10]}"
            now=datetime.datetime.now(UTC).replace(tzinfo=None)
            md=frappe.get_doc({
                "doctype": "Heshly Network Membership",
                "membership_id": mid,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "status": status_val,
                "service_area": service_area[:200] if service_area else location[:200],
                "accepts_network_leads": 1 if accepts_leads else 0,
                "joined_at": now,
                "updated_at": now,
            })
            md.insert(ignore_permissions=True)

        frappe.db.commit()
        # Return serialized
        biz_row=frappe.db.get_value("Business Account", {"business_id": business_id}, ["*"], as_dict=True)
        m_row=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["*"], as_dict=True)
        k_row=frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True)
        return {"success": True, "business": _serialize_business(biz_row, m_row, k_row)}
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback() or str(e), "admin_create_business")
        return {"success": False, "message": str(e)}
    finally:
        try: TenantContext().clear()
        except: pass

@frappe.whitelist()
def admin_update_business(**kwargs):
    _require_system_manager()
    data: dict[str,Any]={}
    for k in ("data","payload","body","$json","json"):
        if k in kwargs and isinstance(kwargs[k], dict):
            data.update(kwargs[k])
    for k,v in kwargs.items():
        if k not in ("cmd","data","payload","body","$json","json") and k not in data:
            data[k]=v
    business_id=_clean(data.get("business_id") or data.get("businessId") or data.get("name") or "")
    if not business_id:
        return {"success": False, "message": "business_id is required"}
    row=frappe.db.get_value("Business Account", {"business_id": business_id}, ["*"], as_dict=True)
    if not row:
        # try by name
        row=frappe.db.get_value("Business Account", business_id, ["*"], as_dict=True)
    if not row:
        return {"success": False, "message": "Business not found"}
    tenant_id=row.get("tenant_id")
    if not tenant_id:
        return {"success": False, "message": "Business has no tenant_id"}

    # Sanitize inputs
    business_name=_clean(data.get("business_name") or data.get("businessName"))
    category=_clean(data.get("category") or data.get("industry"))
    location=_clean(data.get("location"))
    service_area=_clean(data.get("service_area") or data.get("service_areas"))
    phone=_clean(data.get("phone"))
    whatsapp=_clean(data.get("whatsapp") or data.get("whatsapp_number") or data.get("whatsappNumber"))
    email=_clean(data.get("email") or "").lower()
    description=data.get("description")
    services=data.get("services")
    pricing=data.get("pricing") or data.get("price_info")
    status_val=_clean(data.get("status"))

    if business_name is not None and business_name == "":
        return {"success": False, "message": "Business name cannot be empty."}
    if email is not None and email != "" and not _validate_email(email):
        return {"success": False, "message": "Invalid email."}
    if phone is not None and phone != "" and not _validate_phone(phone):
        return {"success": False, "message": "Invalid phone number."}
    if whatsapp is not None and whatsapp != "" and not _validate_phone(whatsapp):
        return {"success": False, "message": "Invalid WhatsApp number."}
    if status_val and status_val not in ("Active","Inactive","Suspended","active","inactive","suspended"):
        return {"success": False, "message": "Invalid status."}
    if services is not None:
        sv=_as_services(services)
        if not sv:
            return {"success": False, "message": "At least one service is required."}
        if len(sv) > 30:
            return {"success": False, "message": "Too many services (max 30)."}
        services=sv
    if pricing is not None and pricing != "" and len(str(pricing)) > 2000:
        return {"success": False, "message": "Pricing info too long."}
    if description is not None and len(str(description)) > 5000:
        return {"success": False, "message": "Description too long."}

    try:
        TenantContext().set(tenant_id)
        doc=frappe.get_doc("Business Account", row["name"])
        if business_name: doc.business_name=business_name[:140]
        if category is not None: doc.industry=category[:100]
        if location is not None: doc.location=location[:200]
        if phone is not None: doc.phone=phone[:30] if phone else None
        if email is not None: doc.email=email.lower()[:140] if email else None
        if status_val: doc.status=status_val.capitalize() if status_val.capitalize() in ("Active","Inactive","Suspended") else status_val
        doc.save(ignore_permissions=True)

        # Knowledge: preserve if not provided
        if services is not None or description is not None or category is not None or pricing is not None or whatsapp is not None or phone is not None:
            # Build final services/desc
            k_row=frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True)
            prev_services=[]
            prev_desc=""
            prev_industry=category or doc.industry or ""
            if k_row:
                try:
                    v=json.loads(k_row.get("services") or "[]")
                    if isinstance(v, list): prev_services=v
                except: pass
                prev_desc=k_row.get("description") or ""
                prev_industry=k_row.get("industry") or prev_industry
            final_services=services if services is not None else prev_services
            final_desc=description if description is not None else prev_desc
            final_industry=category if category is not None else prev_industry
            if pricing is not None and pricing != "":
                # Append pricing to description
                final_desc = (final_desc + "\n\nPricing: " + str(pricing)) if final_desc else f"Pricing: {pricing}"
            # WhatsApp/phone in contact_information
            contact_info={}
            if k_row and k_row.get("contact_information"):
                try:
                    contact_info=json.loads(k_row["contact_information"]) if isinstance(k_row["contact_information"], str) else dict(k_row["contact_information"])
                except: contact_info={}
            if phone is not None: contact_info["phone"]=phone
            if whatsapp is not None: contact_info["whatsapp"]=whatsapp
            if email is not None and email: contact_info["email"]=email
            # Save via BusinessKnowledgeProfile.services
            kp=BusinessKnowledgeProfile(profile_id=tenant_id, tenant_id=tenant_id, business_name=doc.business_name, industry=final_industry or "", description=final_desc or "", services=final_services or [])
            # Preserve products/faqs/policies
            if k_row:
                try:
                    kp.products=json.loads(k_row.get("products") or "[]") if isinstance(k_row.get("products"), str) else (k_row.get("products") or [])
                except: kp.products=[]
                try:
                    kp.faqs=json.loads(k_row.get("faqs") or "[]") if isinstance(k_row.get("faqs"), str) else (k_row.get("faqs") or [])
                except: kp.faqs=[]
                try:
                    kp.policies=json.loads(k_row.get("policies") or "[]") if isinstance(k_row.get("policies"), str) else (k_row.get("policies") or [])
                except: kp.policies=[]
                kp.business_hours={}
                kp.contact_information=contact_info
            else:
                kp.contact_information=contact_info
            TenantAIManager().save_knowledge(kp)

        # Membership service_area / accepts
        if service_area is not None or data.get("accepts_network_leads") is not None or data.get("acceptsNetworkLeads") is not None:
            m_name=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, "name")
            if m_name:
                mdoc=frappe.get_doc("Heshly Network Membership", m_name)
                if service_area is not None:
                    mdoc.service_area=service_area[:200]
                if data.get("accepts_network_leads") is not None or data.get("acceptsNetworkLeads") is not None:
                    val=data.get("accepts_network_leads") if data.get("accepts_network_leads") is not None else data.get("acceptsNetworkLeads")
                    mdoc.accepts_network_leads=1 if val else 0
                mdoc.save(ignore_permissions=True)
        # Status sync to membership
        if status_val:
            try:
                m_name=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, "name")
                if m_name:
                    mdoc=frappe.get_doc("Heshly Network Membership", m_name)
                    # Map Business Account status to membership status
                    st=status_val.capitalize()
                    if st in ("Active","Inactive","Suspended","Paused"):
                        mdoc.status=st
                        mdoc.save(ignore_permissions=True)
            except: pass

        frappe.db.commit()
        biz_row=frappe.db.get_value("Business Account", {"business_id": row["business_id"]}, ["*"], as_dict=True)
        m_row=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, ["*"], as_dict=True)
        k_row=frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["*"], as_dict=True)
        return {"success": True, "business": _serialize_business(biz_row, m_row, k_row)}
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        try: TenantContext().clear()
        except: pass

@frappe.whitelist()
def admin_set_business_status(business_id: str | None = None, status: str | None = None, **kw):
    _require_system_manager()
    bid=_clean(business_id or kw.get("business_id") or kw.get("businessId") or "")
    st=_clean(status or kw.get("status") or "")
    if not bid:
        frappe.throw("business_id is required")
    if st.capitalize() not in ("Active","Inactive","Suspended"):
        frappe.throw("Status must be Active, Inactive or Suspended")
    row=frappe.db.get_value("Business Account", {"business_id": bid}, ["name","tenant_id"], as_dict=True)
    if not row:
        frappe.throw("Business not found", frappe.DoesNotExistError)
    doc=frappe.get_doc("Business Account", row["name"])
    doc.status=st.capitalize()
    doc.save(ignore_permissions=True)
    # Sync membership
    try:
        m_name=frappe.db.get_value("Heshly Network Membership", {"tenant_id": row["tenant_id"]}, "name")
        if m_name:
            mdoc=frappe.get_doc("Heshly Network Membership", m_name)
            mdoc.status=st.capitalize()
            mdoc.save(ignore_permissions=True)
    except: pass
    frappe.db.commit()
    return {"success": True, "business_id": bid, "status": st.capitalize()}

@frappe.whitelist()
def admin_delete_business(business_id: str | None = None, **kw):
    _require_system_manager()
    bid=_clean(business_id or kw.get("business_id") or kw.get("businessId") or kw.get("name") or "")
    if not bid:
        frappe.throw("business_id is required")
    row=frappe.db.get_value("Business Account", {"business_id": bid}, ["name","tenant_id","business_id"], as_dict=True)
    if not row:
        # try by name field
        if frappe.db.exists("Business Account", bid):
            row=frappe.db.get_value("Business Account", bid, ["name","tenant_id","business_id"], as_dict=True)
    if not row:
        frappe.throw("Business not found", frappe.DoesNotExistError)
    tenant_id=row.get("tenant_id") or ""
    # Safeguard: only test businesses can be deleted via admin
    is_test = tenant_id.lower().startswith("test_") or bid.lower().startswith("test_") or tenant_id.lower().startswith("hcn_e2e_") or "e2e" in tenant_id.lower()
    # Also check business_name contains test
    try:
        bname=frappe.db.get_value("Business Account", row["name"], "business_name") or ""
        if "test" in bname.lower():
            is_test=True
    except: pass
    if not is_test:
        frappe.throw("Only test businesses can be deleted via admin. Deactivate non-test businesses instead.", frappe.PermissionError)
    # Delete knowledge, membership, then business and user memberships
    try:
        # Knowledge
        k_name=frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, "name")
        if k_name:
            frappe.delete_doc("Business Knowledge Profile", k_name, ignore_permissions=True, force=True)
        # Membership
        m_name=frappe.db.get_value("Heshly Network Membership", {"tenant_id": tenant_id}, "name")
        if m_name:
            frappe.delete_doc("Heshly Network Membership", m_name, ignore_permissions=True, force=True)
        # User Business Memberships
        for ub in frappe.get_all("User Business Membership", filters={"business_id": bid}, pluck="name"):
            try: frappe.delete_doc("User Business Membership", ub, ignore_permissions=True, force=True)
            except: pass
        for ub in frappe.get_all("User Business Membership", filters={"tenant_id": tenant_id}, pluck="name"):
            try: frappe.delete_doc("User Business Membership", ub, ignore_permissions=True, force=True)
            except: pass
        # Subscription
        for sname in frappe.get_all("Heshly Subscription", filters={"tenant_id": tenant_id}, pluck="name"):
            try: frappe.delete_doc("Heshly Subscription", sname, ignore_permissions=True, force=True)
            except: pass
        for sname in frappe.get_all("Heshly Subscription", filters={"business_id": bid}, pluck="name"):
            try: frappe.delete_doc("Heshly Subscription", sname, ignore_permissions=True, force=True)
            except: pass
        # Business Account last
        frappe.delete_doc("Business Account", row["name"], ignore_permissions=True, force=True)
        frappe.db.commit()
        return {"success": True, "deleted": bid}
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(f"Delete failed: {e}")
