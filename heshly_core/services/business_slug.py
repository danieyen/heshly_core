"""Business public slug — heshly.com/{slug}.

Slug is lowercase letters/numbers/hyphens, unique, stable after name change.
Canonical business_id and tenant_id unchanged.

Reserved slugs = platform routes, never assignable.
"""
from __future__ import annotations

import re

import frappe

# All existing + planned platform paths. Keep in sync with frontend App.tsx
RESERVED_SLUGS = {
    # core platform
    "partner", "login", "signup", "admin", "network", "resources", "blog", "api",
    # auth
    "signin", "sign-in", "signout", "sign-out", "logout", "register",
    # dashboards
    "app", "clients", "erp", "n8n", "dashboard", "me", "settings", "businesses",
    "customers", "leads", "appointments", "calendar", "services", "knowledge",
    "reports", "analytics", "conversations", "simulator", "bookings",
    # marketing
    "privacy-policy", "terms-of-service", "terms", "privacy", "about", "contact",
    "help", "docs", "pricing", "features",
    # system
    "www", "assets", "static", "public", "health", "ping",
}

def _slugify(name: str) -> str:
    raw = (name or "").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-{2,}", "-", raw)
    return raw.strip("-") or "business"

def public_url(slug: str) -> str:
    return f"https://heshly.com/{slug}"

def make_unique_slug(business_name: str, business_id: str | None = None) -> str:
    """Generate a unique, reserved-safe slug for a business.

    - From business_name, hyphenated, lowercased.
    - If reserved or taken by another business, appends -2, -3, ... or business_id suffix.
    - If business already has a slug, return it (stable).
    """
    # If this business already has a slug, keep it
    if business_id:
        row = frappe.db.get_value("Business Account", {"business_id": business_id}, ["public_slug"], as_dict=True)
        if row and row.get("public_slug"):
            return str(row["public_slug"]).strip().lower()

    base = _slugify(business_name)
    # Reserved -> add suffix from business_id last segment or fallback
    if base in RESERVED_SLUGS:
        raw = (business_id or "biz").strip().lower()
        # take last part after _ and clean
        tail = raw.split("_")[-1] if "_" in raw else raw[-6:]
        tail = re.sub(r"[^a-z0-9]+", "-", tail).strip("-") or "biz"
        base = f"{base}-{tail[:8]}"
        if base in RESERVED_SLUGS:
            base = f"{base}-2"

    # Collision check against Business Account.public_slug
    candidate = base
    counter = 2
    # Check existence; if business_id provided, exclude own row
    while True:
        filters = {"public_slug": candidate}
        exists = frappe.db.get_value("Business Account", filters, "name")
        if not exists:
            break
        # If the existing row is the same business, it's not a collision
        if business_id:
            same = frappe.db.get_value("Business Account", {"business_id": business_id}, "name")
            if exists == same:
                break
        candidate = f"{base}-{counter}"
        counter += 1
        if candidate in RESERVED_SLUGS:
            candidate = f"{candidate}-2"

    return candidate

def ensure_slug_for_business(business_id: str) -> str:
    """Ensure a Business Account has a public_slug, creating one if missing."""
    doc = frappe.db.get_value("Business Account", {"business_id": business_id}, ["name","business_name","public_slug","tenant_id"], as_dict=True)
    if not doc:
        raise ValueError(f"Business {business_id} not found")
    if doc.get("public_slug"):
        return str(doc["public_slug"]).strip().lower()
    slug = make_unique_slug(doc.get("business_name") or business_id, business_id)
    # Direct set without validate to avoid TenantContext requirement for existing
    frappe.db.set_value("Business Account", doc["name"], "public_slug", slug)
    frappe.db.commit()
    return slug

def resolve_slug(slug: str) -> dict | None:
    """Resolve public slug to business dict, or None if not found/unpublished."""
    slug = (slug or "").strip().lower()
    if not slug or slug in RESERVED_SLUGS:
        return None
    row = frappe.db.get_value("Business Account", {"public_slug": slug, "status": "Active"}, ["business_id","tenant_id","business_name","public_slug","status","industry","location","email","phone","domain"], as_dict=True)
    if not row:
        return None
    return row
