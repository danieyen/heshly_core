import frappe

from heshly_core.services.website.blog.blog_service import get_published_posts, get_categories


def get_context(context):
    context.no_cache = 1
    page = 1
    try:
        page = int(frappe.form_dict.get("page") or frappe.request.args.get("page") or 1)  # type: ignore
    except Exception:
        page = 1
    category = (frappe.form_dict.get("category") or "").strip() or None
    posts, total, total_pages = get_published_posts(page=page, page_size=9, category=category)
    context.posts = posts
    context.total = total
    context.page = page
    context.total_pages = total_pages
    context.categories = get_categories(published_only=True)
    context.current_category = category
    # SEO
    try:
        ws = frappe.get_single("Heshly Website Settings")
        context.website_settings = ws
        default_title = getattr(ws, "default_meta_title", None) or "Heshly Blog"
        default_desc = getattr(ws, "default_meta_description", None) or "Insights on AI receptionists, customer conversations, and booking automation from Heshly."
    except Exception:
        context.website_settings = None
        default_title = "Heshly Blog"
        default_desc = "Insights on AI receptionists, customer conversations, and booking automation from Heshly."
    context.meta_title = default_title
    context.meta_description = default_desc
    context.canonical_url = "https://heshly.com/blog"
    context.no_sitemap = 0
    return context
