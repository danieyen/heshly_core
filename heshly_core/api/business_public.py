"""Public business pages — heshly.com/{slug}."""
from __future__ import annotations

import frappe

@frappe.whitelist(allow_guest=True)
def get_public_business(slug: str | None = None, **kwargs):
    slug = (slug or kwargs.get("slug") or kwargs.get("business_slug") or "").strip().lower()
    if not slug:
        return {"success": False, "message": "Slug required."}
    # Reserved check is in resolve, but also guard here
    from heshly_core.services.business_slug import resolve_slug, RESERVED_SLUGS
    if slug in RESERVED_SLUGS:
        return {"success": False, "message": "Not found.", "not_found": True}
    row = frappe.db.get_value("Business Account", {"public_slug": slug, "status": "Active"}, ["business_id","business_name","public_slug","industry","location","email","phone","status"], as_dict=True)
    if not row:
        return {"success": False, "message": "Business not found.", "not_found": True}
    tenant_id = frappe.db.get_value("Business Account", {"public_slug": slug}, "tenant_id")
    # Knowledge (public fields only)
    kp = frappe.db.get_value("Business Knowledge Profile", {"tenant_id": tenant_id}, ["business_name","industry","description","services","products"], as_dict=True) if tenant_id else None
    # Parse services/products JSON
    import json
    def _list(v):
        if not v:
            return []
        if isinstance(v, list):
            return v
        try:
            j = json.loads(v)
            return j if isinstance(j, list) else []
        except Exception:
            return []
    services = _list(kp.get("services") if kp else None)
    products = _list(kp.get("products") if kp else None)
    description = (kp.get("description") if kp else "") or ""
    # Only public contact — email/phone from Business Account are public if business opted in via membership
    # For now, expose them as they are the business's own listing data
    return {
        "success": True,
        "business": {
            "business_id": row["business_id"],
            "business_name": row["business_name"],
            "slug": row["public_slug"],
            "public_url": f"https://heshly.com/{row['public_slug']}",
            "industry": row.get("industry"),
            "location": row.get("location"),
            "email": row.get("email"),
            "phone": row.get("phone"),
            "tenant_id": tenant_id,
        },
        "knowledge": {
            "description": description,
            "services": services,
            "products": products,
        },
    }
