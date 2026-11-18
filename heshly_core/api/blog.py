import frappe

from heshly_core.services.website.blog.blog_service import (
    get_categories,
    get_published_posts,
    get_published_post_by_slug,
    get_related_posts,
    blog_meta,
)


@frappe.whitelist(allow_guest=True)
def list_blog_categories():
    return get_categories(published_only=True)


@frappe.whitelist(allow_guest=True)
def list_blog_posts(page: int = 1, page_size: int = 9, category: str | None = None):
    try:
        page = int(page or 1)
        page_size = int(page_size or 9)
    except Exception:
        page, page_size = 1, 9
    posts, total, total_pages = get_published_posts(page=page, page_size=page_size, category=category)
    return {"posts": posts, "total": total, "total_pages": total_pages, "page": page, "page_size": page_size}


@frappe.whitelist(allow_guest=True)
def get_blog_post(slug: str):
    doc = get_published_post_by_slug(slug or "")
    if not doc:
        frappe.throw("Not Found", frappe.DoesNotExistError)
    meta = blog_meta(doc)
    related = get_related_posts(doc, limit=3)
    # Minimal serialized post + meta
    post = {
        "name": doc.name, "title": doc.title, "slug": doc.slug, "excerpt": doc.excerpt,
        "content": doc.content, "featured_image": doc.featured_image, "category": doc.category,
        "author": doc.author, "published": doc.published, "published_on": str(doc.published_on) if doc.published_on else None,
        "reading_time": doc.reading_time, "views": doc.views,
        "meta_title": doc.meta_title, "meta_description": doc.meta_description,
        "canonical_url": meta["canonical"], "social_image": doc.social_image,
    }
    return {"post": post, "meta": meta, "related": related}
