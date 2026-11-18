from __future__ import annotations

import re
import time
from typing import Any

import frappe
import requests

from heshly_core.services.tenant.tenant_context import TenantContext


def _require_tenant_business() -> tuple[str, str, str]:
    """Return (business_id, tenant_id, user) from authenticated session. Raises if not authorized."""
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)
    business_id = frappe.session.data.get("heshly_business_id")
    if not business_id:
        frappe.throw("Business session not found.", frappe.PermissionError)
    business = frappe.db.get_value(
        "Business Account",
        {"business_id": business_id, "status": "Active"},
        ["business_id", "tenant_id", "domain"],
        as_dict=True,
    )
    if not business:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)
    membership = frappe.db.get_value(
        "User Business Membership",
        {"user": frappe.session.user, "business_id": business.business_id, "tenant_id": business.tenant_id, "active": 1},
        ["role"], as_dict=True,
    )
    if not membership:
        frappe.throw("You do not have access to this business.", frappe.PermissionError)
    # Only Owner/Administrator can manage WhatsApp connection
    if membership.role not in ("Owner", "Administrator"):
        frappe.throw("Only the business owner or administrator can manage WhatsApp.", frappe.PermissionError)
    # Ensure TenantContext for downstream permission checks
    try:
        TenantContext().set(business.tenant_id)
    except Exception:
        pass
    return business.business_id, business.tenant_id, frappe.session.user


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    v = str(value)
    if len(v) <= 4:
        return "****"
    return v[:4] + "****" + v[-4:]


@frappe.whitelist(allow_guest=False)
def get_whatsapp_connection():
    """Return current WhatsApp connection for authenticated business. No secrets."""
    business_id, tenant_id, _user = _require_tenant_business()
    # Prefer Number (persistent, has phone_number_id unique)
    row = frappe.db.get_value(
        "Heshly WhatsApp Number",
        {"business_id": business_id, "tenant_id": tenant_id},
        ["number_id", "phone_number", "phone_number_id", "waba_id", "display_name", "verified", "active", "primary", "connection_status"],
        as_dict=True,
    )
    if not row:
        # Fallback: legacy Configuration only
        cfg = frappe.db.get_value(
            "Heshly WhatsApp Configuration",
            {"tenant_id": tenant_id, "active": 1},
            ["configuration_id", "phone_number_id", "business_account_id", "display_phone_number", "active", "verified"],
            as_dict=True,
        )
        if not cfg:
            return {"connected": False, "business_id": business_id, "tenant_id": tenant_id}
        return {
            "connected": bool(cfg.active and cfg.verified),
            "business_id": business_id,
            "tenant_id": tenant_id,
            "phone_number": cfg.display_phone_number,
            "phone_number_id": _mask(cfg.phone_number_id),
            "phone_number_id_full": None,
            "waba_id": _mask(cfg.business_account_id),
            "display_name": None,
            "status": "active" if cfg.active else "disconnected",
        }
    phone = row.phone_number or ""
    # mask phone for display
    masked_phone = phone
    if phone and len(phone) > 6:
        masked_phone = phone[:4] + " *** *** " + phone[-3:]
    return {
        "connected": row.connection_status == "connected" and row.active,
        "business_id": business_id,
        "tenant_id": tenant_id,
        "number_id": row.number_id,
        "phone_number": phone,
        "phone_number_display": masked_phone,
        "phone_number_id": _mask(row.phone_number_id),
        "phone_number_id_full": None,
        "waba_id": _mask(row.waba_id),
        "display_name": row.display_name,
        "verified": bool(row.verified),
        "status": row.connection_status or ("active" if row.active else "disconnected"),
    }



@frappe.whitelist(allow_guest=False)
def list_whatsapp_connections():
    """List all WhatsApp connections for the Heshly platform admin."""
    from heshly_core.api.whatsapp_connect_admin import (
        list_whatsapp_connections as _list_whatsapp_connections,
    )
    return _list_whatsapp_connections()


@frappe.whitelist(allow_guest=False)
def exchange_meta_code(code: str | None = None, redirect_uri: str | None = None, **kwargs):
    """Exchange Meta Embedded Signup code for token, validate ownership, and create mapping.

    Frontend calls FB.login with `config_id` then posts `code` here. Server validates via Graph API.
    Required site_config: meta_app_id, meta_app_secret (or meta_app_id still needed for exchange).
    """
    business_id, tenant_id, _user = _require_tenant_business()

    # Direct phone_number_id path (authorized tenant + uniqueness checks, no Meta code needed) — test / manual onboarding
    if kwargs.get("phone_number_id") or kwargs.get("phoneNumberId"):
        return _create_direct_mapping(business_id, tenant_id, kwargs)

    # Support n8n wrapping / alternate keys for code
    if not code:
        code = kwargs.get("code") or kwargs.get("authorization_code")
    if not code or not str(code).strip():
        frappe.throw("Authorization code is required.", frappe.ValidationError)
    code = str(code).strip()

    site_config = frappe.get_site_config() or {}
    # Try common_site_config fallback
    if not site_config.get("meta_app_id"):
        try:
            import json, os
            # fallback: try reading from frappe.conf directly
            site_config = dict(frappe.conf) if hasattr(frappe, "conf") else site_config
        except Exception:
            pass

    meta_app_id = site_config.get("meta_app_id") or frappe.conf.get("meta_app_id") if hasattr(frappe.conf, "get") else None
    meta_app_secret = site_config.get("meta_app_secret") or (frappe.conf.get("meta_app_secret") if hasattr(frappe.conf, "get") else None)

    if not meta_app_id or not meta_app_secret:
        # No Meta app configured: inform frontend to fallback or configure
        frappe.throw(
            "WhatsApp onboarding is not configured yet. Please contact Heshly support to configure Meta App (meta_app_id, meta_app_secret). Alternatively, use direct phone_number_id mapping for testing.",
            frappe.ValidationError,
        )

    # Exchange code for access token
    token_url = "https://graph.facebook.com/v23.0/oauth/access_token"
    params = {
        "client_id": meta_app_id,
        "client_secret": meta_app_secret,
        "code": code,
    }
    if redirect_uri:
        params["redirect_uri"] = redirect_uri

    try:
        resp = requests.get(token_url, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Meta token exchange failed")
        frappe.throw(f"Meta token exchange failed: {e}", frappe.ValidationError)

    if "error" in data:
        frappe.log_error(str(data), "Meta token exchange error")
        frappe.throw(f"Meta authorization failed: {data['error'].get('message', str(data['error']))}", frappe.ValidationError)

    access_token = data.get("access_token")
    if not access_token:
        frappe.throw("Meta did not return an access token.", frappe.ValidationError)

    # Use token to fetch WABA and phone numbers — validate ownership
    # Step 1: debug_token to get user/app info (optional)
    # Step 2: fetch phone numbers associated with this grant
    # Meta Embedded Signup returns WABA via subscribed_apps or via user's business
    # Try: GET /me?fields=id,name and GET /debug_token
    # Then: GET /{user-id}/assigned_businesses or GET /me/businesses
    # Simpler: try to get phone numbers via GET /{waba_id}/phone_numbers if waba_id known via kwargs, else discover

    # If frontend provided waba_id/phone_number_id alongside code, validate those specific ones
    waba_id_hint = kwargs.get("waba_id") or kwargs.get("business_account_id") or kwargs.get("wabaId")
    phone_number_id_hint = kwargs.get("phone_number_id") or kwargs.get("phoneNumberId")

    validated = None
    try:
        validated = _validate_and_fetch_numbers(access_token, waba_id_hint, phone_number_id_hint)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Meta validation failed")
        frappe.throw(f"Could not validate WhatsApp number with Meta: {e}", frappe.ValidationError)

    if not validated:
        frappe.throw("Could not find WhatsApp number for this authorization.", frappe.ValidationError)

    phone_number_id = validated["phone_number_id"]
    waba_id = validated["waba_id"]
    phone_number = validated.get("phone_number", "")
    display_name = validated.get("display_name", "")

    # Cross-tenant uniqueness: phone_number_id must not be claimed by another tenant (active)
    existing = frappe.db.get_value(
        "Heshly WhatsApp Number",
        {"phone_number_id": phone_number_id, "active": 1},
        ["tenant_id", "business_id"],
        as_dict=True,
    )
    if existing and existing.tenant_id != tenant_id:
        frappe.throw(f"This WhatsApp number is already connected to another business.", frappe.ValidationError)

    existing_cfg = frappe.db.get_value(
        "Heshly WhatsApp Configuration",
        {"phone_number_id": phone_number_id, "active": 1},
        ["tenant_id", "configuration_id"],
        as_dict=True,
    )
    if existing_cfg and existing_cfg.tenant_id != tenant_id:
        frappe.throw(f"This WhatsApp number is already connected to another business.", frappe.ValidationError)

    # Create/update Configuration + Number atomically
    return _upsert_mapping(
        business_id=business_id,
        tenant_id=tenant_id,
        phone_number_id=phone_number_id,
        waba_id=waba_id,
        phone_number=phone_number,
        display_name=display_name,
        access_token=access_token,
    )


def _validate_and_fetch_numbers(access_token: str, waba_id_hint: str | None, phone_number_id_hint: str | None) -> dict | None:
    """Validate token ownership by querying Graph API."""

    if phone_number_id_hint:
        if not waba_id_hint:
            raise ValueError("WABA ID is required when validating a phone_number_id.")

        phone_url = f"https://graph.facebook.com/v23.0/{phone_number_id_hint}"
        phone_params = {
            "fields": "id,display_phone_number,verified_name,code_verification_status",
            "access_token": access_token,
        }

        r = requests.get(phone_url, params=phone_params, timeout=10)
        j = r.json()

        if "error" in j:
            raise ValueError(j["error"].get("message", str(j["error"])))

        waba_url = f"https://graph.facebook.com/v23.0/{waba_id_hint}/phone_numbers"
        wr = requests.get(waba_url, params={"access_token": access_token}, timeout=10)
        wj = wr.json()

        if "error" in wj:
            raise ValueError(wj["error"].get("message", str(wj["error"])))

        matched = next((n for n in wj.get("data", []) if str(n.get("id")) == str(phone_number_id_hint)), None)

        if not matched:
            raise ValueError("The supplied phone number does not belong to the supplied WABA.")

        return {
            "phone_number_id": str(phone_number_id_hint),
            "waba_id": str(waba_id_hint),
            "phone_number": matched.get("display_phone_number") or j.get("display_phone_number") or "",
            "display_name": matched.get("verified_name") or j.get("verified_name") or "",
        }

    if waba_id_hint:
        url = f"https://graph.facebook.com/v23.0/{waba_id_hint}/phone_numbers"
        r = requests.get(url, params={"access_token": access_token}, timeout=10)
        j = r.json()

        if "error" in j:
            raise ValueError(j["error"].get("message", str(j["error"])))

        data = j.get("data", [])
        if not data:
            return None

        first = data[0]
        return {
            "phone_number_id": str(first.get("id", "")),
            "waba_id": str(waba_id_hint),
            "phone_number": first.get("display_phone_number", ""),
            "display_name": first.get("verified_name", ""),
        }

    return None

def _create_direct_mapping(business_id: str, tenant_id: str, kwargs: dict) -> dict:
    """Create mapping directly from provided phone_number_id (dev/testing). Still enforces uniqueness and tenant derivation."""
    phone_number_id = str(kwargs.get("phone_number_id") or kwargs.get("phoneNumberId") or "").strip()
    waba_id = str(kwargs.get("waba_id") or kwargs.get("business_account_id") or kwargs.get("wabaId") or "").strip()
    phone_number = str(kwargs.get("phone_number") or kwargs.get("phoneNumber") or kwargs.get("phone") or "").strip()
    display_name = str(kwargs.get("display_name") or kwargs.get("displayName") or "").strip()
    access_token = str(kwargs.get("access_token") or kwargs.get("accessToken") or "").strip()
    if not phone_number_id:
        frappe.throw("phone_number_id is required.", frappe.ValidationError)
    if not phone_number:
        phone_number = phone_number_id  # fallback
    # Uniqueness checks
    existing = frappe.db.get_value("Heshly WhatsApp Number", {"phone_number_id": phone_number_id, "active": 1}, ["tenant_id"], as_dict=True)
    if existing and existing.tenant_id != tenant_id:
        frappe.throw("This WhatsApp number is already connected to another business.", frappe.ValidationError)
    existing_cfg = frappe.db.get_value("Heshly WhatsApp Configuration", {"phone_number_id": phone_number_id, "active": 1}, ["tenant_id"], as_dict=True)
    if existing_cfg and existing_cfg.tenant_id != tenant_id:
        frappe.throw("This WhatsApp number is already connected to another business.", frappe.ValidationError)
    return _upsert_mapping(
        business_id=business_id,
        tenant_id=tenant_id,
        phone_number_id=phone_number_id,
        waba_id=waba_id,
        phone_number=phone_number,
        display_name=display_name,
        access_token=access_token,
    )


def _upsert_mapping(business_id: str, tenant_id: str, phone_number_id: str, waba_id: str, phone_number: str, display_name: str, access_token: str) -> dict:
    """Atomically create/update Number + Configuration for this tenant."""
    now = frappe.utils.now()
    # Use frappe.db transaction
    try:
        frappe.db.begin()
    except Exception:
        pass

    # 1. Upsert Configuration
    cfg_name = frappe.db.get_value("Heshly WhatsApp Configuration", {"tenant_id": tenant_id, "phone_number_id": phone_number_id}, "name")
    if not cfg_name:
        # Also check if an active config exists for this tenant with different phone_number_id — reuse or create new
        cfg_name = frappe.db.get_value("Heshly WhatsApp Configuration", {"tenant_id": tenant_id, "active": 1}, "name")

    if cfg_name:
        doc = frappe.get_doc("Heshly WhatsApp Configuration", cfg_name)
        doc.phone_number_id = phone_number_id
        doc.business_account_id = waba_id or doc.business_account_id
        if display_name:
            doc.display_phone_number = phone_number or doc.display_phone_number
        elif phone_number:
            doc.display_phone_number = phone_number
        doc.active = 1
        doc.verified = 1
        if access_token:
            doc.access_token = access_token
        # app_secret/verify_token keep existing unless provided
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.new_doc("Heshly WhatsApp Configuration")
        doc.configuration_id = f"cfg_{business_id}_{int(time.time())}"
        doc.tenant_id = tenant_id
        doc.phone_number_id = phone_number_id
        doc.business_account_id = waba_id
        if hasattr(doc, "business_id"):
            try:
                doc.business_id = business_id  # required after Number migration added business_id to Configuration table
            except Exception:
                pass
        doc.access_token = access_token or f"pending_{phone_number_id}"
        doc.verify_token = f"verify_{business_id}"
        doc.app_secret = ""
        doc.display_phone_number = phone_number
        doc.active = 1
        doc.verified = 1
        doc.api_version = "v23.0"
        doc.insert(ignore_permissions=True)

    configuration_id = doc.configuration_id if hasattr(doc, "configuration_id") else doc.name

    # 2. Upsert Number (persistent)
    num_name = frappe.db.get_value("Heshly WhatsApp Number", {"tenant_id": tenant_id, "phone_number_id": phone_number_id}, "name")
    if not num_name:
        num_name = frappe.db.get_value("Heshly WhatsApp Number", {"tenant_id": tenant_id, "business_id": business_id}, "name")

    if num_name:
        nd = frappe.get_doc("Heshly WhatsApp Number", num_name)
        nd.business_id = business_id
        nd.configuration_id = configuration_id
        nd.phone_number = phone_number
        nd.phone_number_id = phone_number_id
        nd.waba_id = waba_id
        nd.display_name = display_name or nd.display_name or phone_number
        nd.connection_status = "connected"
        nd.active = 1
        nd.primary = 1
        nd.verified = 1
        nd.save(ignore_permissions=True)
    else:
        nd = frappe.new_doc("Heshly WhatsApp Number")
        nd.number_id = f"num_{business_id}_{int(time.time())}"
        nd.tenant_id = tenant_id
        nd.business_id = business_id
        nd.configuration_id = configuration_id
        nd.phone_number = phone_number
        nd.phone_number_id = phone_number_id
        nd.waba_id = waba_id
        nd.display_name = display_name or phone_number
        nd.connection_status = "connected"
        nd.active = 1
        nd.primary = 1
        nd.verified = 1
        nd.insert(ignore_permissions=True)

    try:
        frappe.db.commit()
    except Exception:
        pass

    return {
        "success": True,
        "business_id": business_id,
        "tenant_id": tenant_id,
        "phone_number_id": phone_number_id,
        "phone_number": phone_number,
        "waba_id": waba_id,
        "configuration_id": configuration_id,
        "number_id": nd.number_id if hasattr(nd, "number_id") else nd.name,
    }


@frappe.whitelist(allow_guest=False)
def disconnect_whatsapp():
    """Disconnect current business WhatsApp (soft delete)."""
    business_id, tenant_id, _user = _require_tenant_business()
    # Deactivate Number(s)
    names = frappe.get_all("Heshly WhatsApp Number", filters={"tenant_id": tenant_id, "business_id": business_id, "active": 1}, pluck="name")
    for name in names:
        try:
            doc = frappe.get_doc("Heshly WhatsApp Number", name)
            doc.active = 0
            doc.connection_status = "disconnected"
            doc.save(ignore_permissions=True)
        except Exception:
            pass
    # Deactivate Configuration(s)
    cfg_names = frappe.get_all("Heshly WhatsApp Configuration", filters={"tenant_id": tenant_id, "active": 1}, pluck="name")
    for name in cfg_names:
        try:
            doc = frappe.get_doc("Heshly WhatsApp Configuration", name)
            doc.active = 0
            doc.save(ignore_permissions=True)
        except Exception:
            pass
    try:
        frappe.db.commit()
    except Exception:
        pass
    return {"success": True, "business_id": business_id, "tenant_id": tenant_id, "connected": False}

@frappe.whitelist(allow_guest=False)
def get_meta_embedded_signup_config():
    """Return only public Meta Embedded Signup configuration to the frontend."""
    _require_tenant_business()

    site_config = frappe.get_site_config() or {}
    meta_app_id = site_config.get("meta_app_id")
    meta_config_id = site_config.get("meta_config_id")

    if not meta_app_id or not meta_config_id:
        frappe.throw(
            "Meta Embedded Signup is not configured.",
            frappe.ValidationError,
        )

    return {
        "meta_app_id": str(meta_app_id),
        "meta_config_id": str(meta_config_id),
    }
