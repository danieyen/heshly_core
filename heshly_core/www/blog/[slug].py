import frappe

from heshly_core.services.website.blog.blog_service import get_published_post_by_slug, get_related_posts, increment_view_count, blog_meta


def get_context(context, slug):
    # Validate slug format
    import re
    if not slug or not re.match(r"^[a-z0-9\-]+$", slug.lower()):
        frappe.local.flags.redirect_location = "/404"
        raise frappe.DoesNotExistError
    doc = get_published_post_by_slug(slug.lower())
    if not doc:
        frappe.local.flags.redirect_location = "/404"
        raise frappe.DoesNotExistError
    # Increment views (async best-effort)
    try:
        increment_view_count(doc.name)
    except Exception:
        pass
    context.doc = doc
    context.related = get_related_posts(doc, limit=3)
    meta = blog_meta(doc)
    context.meta_title = meta["title"]
    context.meta_description = meta["description"]
    context.canonical_url = meta["canonical"]
    context.blog_meta = meta
    # JSON-LD structured data
    import html as _html
    import json as _json

    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": doc.title,
        "description": meta["description"],
        "image": meta["image"],
        "datePublished": str(doc.published_on) if doc.published_on else None,
        "author": {"@type": "Person", "name": doc.author or "Heshly"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": meta["canonical"]},
    }
    # Compact None
    ld = {k: v for k, v in ld.items() if v is not None}
    context.blog_ld_json = _json.dumps(ld, ensure_ascii=False)
    context.no_cache = 1
    context.no_sitemap = 0
    return context
