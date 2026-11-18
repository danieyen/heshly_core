"""Add public_slug to Business Account and backfill existing."""
import frappe

def execute():
    if not frappe.db.table_exists("Business Account"):
        return
    # Add column if missing
    cols = frappe.db.sql("SHOW COLUMNS FROM `tabBusiness Account`", as_dict=True) or []
    names = {c["Field"] for c in cols}
    if "public_slug" not in names:
        frappe.db.sql("ALTER TABLE `tabBusiness Account` ADD COLUMN `public_slug` VARCHAR(140)")
        frappe.db.commit()
    # Create index for slug uniqueness (allow nulls)
    try:
        frappe.db.sql("CREATE UNIQUE INDEX IF NOT EXISTS idx_business_public_slug ON `tabBusiness Account` (public_slug)")
    except Exception:
        try:
            frappe.db.sql("CREATE UNIQUE INDEX idx_business_public_slug ON `tabBusiness Account` (public_slug)")
        except Exception:
            pass
    frappe.db.commit()

    # Backfill missing slugs
    try:
        from heshly_core.services.business_slug import make_unique_slug
        rows = frappe.db.sql("SELECT name, business_id, business_name FROM `tabBusiness Account` WHERE public_slug IS NULL OR public_slug = ''", as_dict=True) or []
        for r in rows:
            try:
                slug = make_unique_slug(r.get("business_name") or r["business_id"], r["business_id"])
                frappe.db.set_value("Business Account", r["name"], "public_slug", slug)
            except Exception:
                continue
        frappe.db.commit()
    except Exception:
        pass
