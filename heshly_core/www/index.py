import frappe
def get_context(context):
    context.no_cache = 1
    context.no_sitemap = 0
    # SEO from Website Settings if exists
    try:
        ws = frappe.get_single("Heshly Website Settings")
        context.website_settings = ws
    except Exception:
        context.website_settings = None
    return context
