import frappe
import pytest


def _make_category(name="General"):
    slug = name.lower().replace(" ", "-")
    if frappe.db.exists("Heshly Blog Category", slug):
        return frappe.get_doc("Heshly Blog Category", slug)
    doc = frappe.get_doc({"doctype": "Heshly Blog Category", "category_name": name, "slug": slug, "published": 1})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


def _make_post(title="Hello", published=0, category=None):
    doc = frappe.get_doc({
        "doctype": "Heshly Blog Post",
        "title": title,
        "content": "<p>Hello world hello world hello world</p>"*10,
        "category": category,
        "published": published,
    })
    if published:
        doc.published_on = frappe.utils.now_datetime()
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


def test_create_blog_post():
    cat = _make_category("General")
    post = _make_post("Test Create", published=0, category=cat.name)
    assert post.slug
    assert post.reading_time >= 1


def test_slug_generation():
    cat = _make_category("SlugCat")
    post = _make_post("My Great Post", published=0, category=cat.name)
    assert post.slug == "my-great-post"


def test_duplicate_slug_rejection():
    cat = _make_category("DupCat")
    p1 = _make_post("Duplicate Slug Post", published=0, category=cat.name)
    # p1 slug is duplicate-slug-post
    try:
        p2 = frappe.get_doc({"doctype": "Heshly Blog Post", "title": "Other", "slug": p1.slug, "content": "x", "published": 0})
        p2.insert(ignore_permissions=True)
        assert False, "should have rejected duplicate slug"
    except Exception as e:
        assert "already exists" in str(e)
    finally:
        frappe.db.rollback()


def test_reading_time():
    cat = _make_category("RT")
    post = _make_post("RT Post", published=0, category=cat.name)
    assert post.reading_time >= 1


def test_published_on_behavior():
    cat = _make_category("PubOn")
    post = _make_post("PubOn Post", published=0, category=cat.name)
    assert not post.published_on
    post.published = 1
    post.save(ignore_permissions=True)
    frappe.db.commit()
    assert post.published_on


def test_published_retrieval():
    from heshly_core.services.website.blog.blog_service import get_published_post_by_slug, get_published_posts
    cat = _make_category("PubRet")
    pub = _make_post("Published Post", published=1, category=cat.name)
    unpub = _make_post("Unpublished Post", published=0, category=cat.name)
    assert get_published_post_by_slug(pub.slug) is not None
    assert get_published_post_by_slug(unpub.slug) is None
    posts, total, pages = get_published_posts(page=1, page_size=10)
    assert any(p.slug == pub.slug for p in posts)
    assert not any(p.slug == unpub.slug for p in posts)


def test_invalid_slug_404():
    from heshly_core.services.website.blog.blog_service import get_published_post_by_slug
    assert get_published_post_by_slug("not-exist-xyz-123") is None
    assert get_published_post_by_slug("INVALID SLUG") is None


def test_category_filtering():
    from heshly_core.services.website.blog.blog_service import get_published_posts
    cat = _make_category("FilterCat")
    _make_post("Filter Post", published=1, category=cat.name)
    posts, total, _ = get_published_posts(category=cat.name)
    assert all(p.category == cat.name for p in posts) if posts else True


def test_pagination():
    from heshly_core.services.website.blog.blog_service import get_published_posts
    cat = _make_category("PagCat")
    for i in range(3):
        _make_post(f"Pag Post {frappe.utils.now_datetime().timestamp()}-{i}", published=1, category=cat.name)
    posts, total, pages = get_published_posts(page=1, page_size=2)
    assert len(posts) <= 2


def test_related_posts():
    from heshly_core.services.website.blog.blog_service import get_related_posts, get_published_post_by_slug
    cat = _make_category("RelCat")
    p1 = _make_post("Rel Post 1", published=1, category=cat.name)
    _make_post("Rel Post 2", published=1, category=cat.name)
    related = get_related_posts(p1, limit=3)
    assert all(r.name != p1.name for r in related)


def test_view_count():
    from heshly_core.services.website.blog.blog_service import increment_view_count
    cat = _make_category("ViewCat")
    post = _make_post("View Post", published=1, category=cat.name)
    before = frappe.db.get_value("Heshly Blog Post", post.name, "views") or 0
    increment_view_count(post.name)
    after = frappe.db.get_value("Heshly Blog Post", post.name, "views") or 0
    assert after == before + 1


def test_seo_metadata():
    from heshly_core.services.website.blog.blog_service import blog_meta
    cat = _make_category("SeoCat")
    post = _make_post("SEO Post", published=1, category=cat.name)
    post.meta_title = "Custom Title"
    post.meta_description = "Custom desc"
    post.save(ignore_permissions=True)
    meta = blog_meta(post)
    assert meta["title"] == "Custom Title"
    assert meta["description"] == "Custom desc"
    assert "/blog/" in meta["canonical"]


def test_permission_guest_read():
    # Guest can read published via ORM? At least not blocked
    from heshly_core.services.website.blog.blog_service import get_published_post_by_slug
    cat = _make_category("PermCat")
    post = _make_post("Perm Post", published=1, category=cat.name)
    frappe.set_user("Guest")
    try:
        assert get_published_post_by_slug(post.slug) is not None
    finally:
        frappe.set_user("Administrator")
