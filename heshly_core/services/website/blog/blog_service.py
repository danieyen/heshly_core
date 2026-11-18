from __future__ import annotations

import html
import re

import frappe


def _excerpt_or_fallback(doc, length: int = 160) -> str:
    if getattr(doc, "excerpt", None):
        return doc.excerpt
    text = re.sub(r"<[^>]+>", " ", getattr(doc, "content", "") or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length]


def blog_meta(doc) -> dict:
    """Generate SEO metadata for a published post."""
    title = (getattr(doc, "meta_title", None) or getattr(doc, "title", "") or "Heshly Blog").strip()
    description = (getattr(doc, "meta_description", None) or _excerpt_or_fallback(doc)).strip()
    slug = getattr(doc, "slug", "")
    canonical = getattr(doc, "canonical_url", None)
    if not canonical:
        canonical = f"https://heshly.com/blog/{slug}" if slug else "https://heshly.com/blog"
    image = getattr(doc, "social_image", None) or getattr(doc, "featured_image", None) or "/assets/heshly_core/heshly_landing/logo.svg"
    social_title = (getattr(doc, "social_title", None) or title or "").strip()
    social_desc = (getattr(doc, "social_description", None) or description or "").strip()
    return {
        "title": html.escape(title),
        "description": html.escape(description),
        "canonical": canonical,
        "og_title": html.escape(social_title),
        "og_description": html.escape(social_desc),
        "og_image": image,
        "slug": slug,
        "image": image,
    }


def get_categories(published_only: bool = True):
    filters = {"published": 1} if published_only else {}
    try:
        # Cache categories for 5 minutes
        cache_key = "heshly_blog_categories"
        if published_only and frappe.cache().get_value(cache_key):
            return frappe.cache().get_value(cache_key)
        cats = frappe.get_all(
            "Heshly Blog Category",
            filters=filters,
            fields=["name", "category_name", "slug", "description", "published", "sort_order"],
            order_by="sort_order asc, category_name asc",
        )
        if published_only:
            frappe.cache().set_value(cache_key, cats, expires_in_sec=300)
        return cats
    except Exception:
        return []


def get_published_posts(page: int = 1, page_size: int = 9, category: str | None = None):
    page = max(1, int(page or 1))
    page_size = max(1, min(24, int(page_size or 9)))
    filters: dict = {"published": 1}
    if category:
        filters["category"] = category
    fields = [
        "name", "title", "slug", "excerpt", "featured_image",
        "category", "author", "published_on", "reading_time", "views",
    ]
    try:
        posts = frappe.get_all(
            "Heshly Blog Post",
            filters=filters,
            fields=fields,
            order_by="published_on desc, creation desc",
            limit_start=(page - 1) * page_size,
            limit_page_length=page_size,
        )
        total = frappe.db.count("Heshly Blog Post", filters=filters)
        return posts, total, (total + page_size - 1) // page_size if total else 1
    except Exception:
        return [], 0, 1


def get_published_post_by_slug(slug: str):
    slug = (slug or "").strip().lower()
    if not slug or not re.match(r"^[a-z0-9\-]+$", slug):
        return None
    try:
        doc = frappe.get_doc("Heshly Blog Post", {"slug": slug, "published": 1})
        if not doc or not doc.published:
            return None
        return doc
    except Exception:
        return None


def get_posts_by_category(category: str, page: int = 1, page_size: int = 9):
    return get_published_posts(page=page, page_size=page_size, category=category)


def get_related_posts(doc, limit: int = 3):
    try:
        filters: dict = {"published": 1, "name": ["!=", doc.name]}
        if getattr(doc, "category", None):
            # Prefer same category
            filters["category"] = doc.category
        posts = frappe.get_all(
            "Heshly Blog Post",
            filters=filters,
            fields=["name", "title", "slug", "featured_image", "excerpt", "category", "published_on", "reading_time"],
            order_by="published_on desc, creation desc",
            limit_page_length=limit,
        )
        if len(posts) < limit and getattr(doc, "category", None):
            # Fill with other categories if needed
            remaining = limit - len(posts)
            other = frappe.get_all(
                "Heshly Blog Post",
                filters={"published": 1, "category": ["!=", doc.category], "name": ["!=", doc.name]},
                fields=["name", "title", "slug", "featured_image", "excerpt", "category", "published_on", "reading_time"],
                order_by="published_on desc, creation desc",
                limit_page_length=remaining,
            )
            posts.extend(other)
        return posts[:limit]
    except Exception:
        return []


def increment_view_count(name: str):
    try:
        frappe.db.sql("UPDATE `tabHeshly Blog Post` SET `views` = COALESCE(`views`,0) + 1 WHERE `name`=%s", (name,))
        frappe.db.commit()
    except Exception:
        pass
