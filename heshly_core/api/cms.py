from __future__ import annotations

import re
import json

import frappe
from frappe.utils import slug as frappe_slug


def _require_system_manager():
	if frappe.session.user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)
	roles = frappe.get_roles(frappe.session.user)
	if "System Manager" not in roles and "Administrator" not in roles:
		frappe.throw("Not permitted", frappe.PermissionError)


def _normalize_slug(s: str) -> str:
	s = (s or "").strip().lower()
	s = re.sub(r"[^a-z0-9\-]+", "-", s)
	s = re.sub(r"-{2,}", "-", s).strip("-")
	return s


_ALLOWED_CONTENT_TAGS = {
	"p", "br", "strong", "em", "u", "a", "ul", "ol", "li", "blockquote",
	"h1", "h2", "h3", "h4", "h5", "h6", "img", "code", "pre", "span", "div",
	"table", "thead", "tbody", "tr", "td", "th", "hr", "sup", "sub",
}
_ALLOWED_CONTENT_ATTRS = {
	"a": ["href", "target", "rel"],
	"img": ["src", "alt", "title", "width", "height"],
	"th": ["colspan", "rowspan"],
	"td": ["colspan", "rowspan"],
}


def _sanitize_content(html: str) -> str:
	"""Sanitize article HTML server-side without breaking legitimate formatting.
	Removes script/style, event handlers, javascript: URLs. Keeps headings/lists/links/img/blockquote/table.
	"""
	if not html or not isinstance(html, str):
		return html
	try:
		import nh3
		return nh3.clean(
			html,
			tags=_ALLOWED_CONTENT_TAGS,
			attributes=_ALLOWED_CONTENT_ATTRS,
			url_schemes={"http", "https", "mailto", "tel"},
			link_rel="noopener noreferrer",
		)
	except Exception:
		# Fallback: strip script tags and event handlers via regex if nh3 unavailable
		s = re.sub(r"<script[^>]*>.*?</script\s*>", "", html, flags=re.IGNORECASE | re.DOTALL)
		s = re.sub(r"\s+on\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", "", s, flags=re.IGNORECASE)
		s = re.sub(r"javascript\s*:", "", s, flags=re.IGNORECASE)
		return s


def _is_manager() -> bool:
	if frappe.session.user == "Guest":
		return False
	roles = frappe.get_roles(frappe.session.user) or []
	return "System Manager" in roles or "Administrator" in roles


@frappe.whitelist(allow_guest=True)
def is_admin():
	"""Check if current user is System Manager."""
	if frappe.session.user == "Guest":
		return {"success": False, "user": "Guest", "is_admin": False}
	roles = frappe.get_roles(frappe.session.user) or []
	is_adm = "System Manager" in roles or "Administrator" in roles
	return {"success": True, "user": frappe.session.user, "is_admin": is_adm}


def _serialize_post(doc, include_content: bool = True) -> dict:
	d = {
		"name": doc.name,
		"title": doc.title,
		"slug": doc.slug,
		"excerpt": doc.excerpt,
		"featured_image": doc.featured_image,
		"category": doc.category,
		"author": doc.author,
		"published": int(doc.published or 0),
		"published_on": str(doc.published_on) if doc.published_on else None,
		"meta_title": doc.meta_title,
		"meta_description": doc.meta_description,
		"meta_keywords": doc.meta_keywords,
		"canonical_url": doc.canonical_url,
		"social_title": doc.social_title,
		"social_description": doc.social_description,
		"social_image": doc.social_image,
		"reading_time": doc.reading_time,
		"views": doc.views,
		"creation": str(doc.creation) if doc.creation else None,
		"modified": str(doc.modified) if doc.modified else None,
	}
	if include_content:
		d["content"] = doc.content
	# tags child table
	tags = []
	try:
		for row in (doc.tags or []):
			tags.append({"tag": row.tag, "tag_name": row.tag_name})
	except Exception:
		pass
	d["tags"] = tags
	return d


def _tags_from_payload(payload: dict) -> list[str]:
	tags = payload.get("tags")
	if tags is None:
		tags = payload.get("tag_list") or payload.get("tag") or []
	if isinstance(tags, str):
		try:
			parsed = json.loads(tags)
			if isinstance(parsed, list):
				tags = parsed
			else:
				tags = [tags]
		except Exception:
			tags = [t.strip() for t in tags.split(",") if t.strip()]
	if not isinstance(tags, list):
		tags = [tags] if tags else []
	# normalize: list of slugs or tag names; we expect slugs/names of existing Heshly Blog Tag
	out = []
	for t in tags:
		if isinstance(t, dict):
			# allow {tag: slug}
			v = t.get("tag") or t.get("slug") or t.get("tag_name") or t.get("name")
			if v:
				out.append(str(v).strip())
		elif isinstance(t, str) and t.strip():
			out.append(t.strip())
	return out


@frappe.whitelist()
def list_posts(page: int = 1, page_size: int = 20, search: str | None = None, category: str | None = None, published: int | None = None):
	_require_system_manager()
	try:
		page = int(page or 1)
		page_size = int(page_size or 20)
	except Exception:
		page, page_size = 1, 20
	page = max(1, page)
	page_size = max(1, min(100, page_size))
	filters: dict = {}
	if category:
		filters["category"] = category
	if published is not None and str(published) != "":
		try:
			published = int(published)
			if published in (0, 1):
				filters["published"] = published
		except Exception:
			pass
	# search across title/slug
	or_filters = None
	if search and str(search).strip():
		s = str(search).strip()
		# use frappe.get_all with or_filters via sql? fallback to client filter via db.sql
		# We'll do a db.sql search for performance
		cond = ""
		args: list = []
		where = []
		if filters.get("category"):
			where.append("category=%s")
			args.append(filters["category"])
		if "published" in filters:
			where.append("published=%s")
			args.append(filters["published"])
		base_where = (" WHERE " + " AND ".join(where)) if where else ""
		# add search
		search_like = f"%{s}%"
		search_clause = "(title LIKE %s OR slug LIKE %s OR excerpt LIKE %s)"
		if base_where:
			where_sql = base_where + f" AND {search_clause}"
		else:
			where_sql = f" WHERE {search_clause}"
		args_search = args + [search_like, search_like, search_like]
		count_sql = f"SELECT COUNT(*) as c FROM `tabHeshly Blog Post` {where_sql}"
		count = frappe.db.sql(count_sql, tuple(args_search), as_dict=True)
		total = int(count[0]["c"] if count else 0)
		fields = "name, title, slug, excerpt, featured_image, category, author, published, published_on, reading_time, views, creation, modified"
		q = f"SELECT {fields} FROM `tabHeshly Blog Post` {where_sql} ORDER BY modified DESC LIMIT %s OFFSET %s"
		rows = frappe.db.sql(q, tuple(args_search + [page_size, (page - 1) * page_size]), as_dict=True)
		# enrich tags
		posts = []
		for r in rows:
			try:
				doc = frappe.get_doc("Heshly Blog Post", r["name"])
				posts.append(_serialize_post(doc, include_content=False))
			except Exception:
				posts.append({**r, "tags": []})
		total_pages = (total + page_size - 1) // page_size if total else 1
		return {"posts": posts, "total": total, "total_pages": total_pages, "page": page, "page_size": page_size}
	# no search
	try:
		posts_docs = frappe.get_all(
			"Heshly Blog Post",
			filters=filters if filters else None,
			fields=["name", "title", "slug", "excerpt", "featured_image", "category", "author", "published", "published_on", "reading_time", "views", "creation", "modified"],
			order_by="modified desc",
			limit_start=(page - 1) * page_size,
			limit_page_length=page_size,
		)
		total = frappe.db.count("Heshly Blog Post", filters=filters if filters else None)
		posts = []
		for r in posts_docs:
			try:
				doc = frappe.get_doc("Heshly Blog Post", r["name"])
				posts.append(_serialize_post(doc, include_content=False))
			except Exception:
				posts.append({**r, "tags": []})
		total_pages = (total + page_size - 1) // page_size if total else 1
		return {"posts": posts, "total": int(total), "total_pages": total_pages, "page": page, "page_size": page_size}
	except Exception as e:
		frappe.throw(str(e))


@frappe.whitelist()
def get_post(name: str | None = None, slug: str | None = None):
	_require_system_manager()
	if not name and not slug:
		frappe.throw("name or slug required")
	doc = None
	if name:
		doc = frappe.get_doc("Heshly Blog Post", name)
	elif slug:
		slug = _normalize_slug(slug)
		doc = frappe.get_doc("Heshly Blog Post", {"slug": slug})
	if not doc:
		frappe.throw("Not Found", frappe.DoesNotExistError)
	return _serialize_post(doc, include_content=True)


@frappe.whitelist()
def create_post(**kwargs):
	_require_system_manager()
	# unwrap JSON string payloads
	data = dict(kwargs)
	# frappe may send `data` as JSON string
	if "data" in data and isinstance(data["data"], str):
		try:
			parsed = json.loads(data["data"])
			if isinstance(parsed, dict):
				data.update(parsed)
		except Exception:
			pass
	# also handle single JSON arg
	for k, v in list(data.items()):
		if isinstance(v, str) and v.strip().startswith("{"):
			try:
				pv = json.loads(v)
				if isinstance(pv, dict) and k in ("payload", "doc", "post"):
					data.update(pv)
			except Exception:
				pass
	title = (data.get("title") or "").strip()
	slug = _normalize_slug(str(data.get("slug") or title))
	content = data.get("content") or ""
	excerpt = data.get("excerpt")
	featured_image = data.get("featured_image")
	category = data.get("category")
	author = data.get("author") or frappe.session.user
	meta_title = data.get("meta_title")
	meta_description = data.get("meta_description")
	meta_keywords = data.get("meta_keywords")
	canonical_url = data.get("canonical_url")
	social_title = data.get("social_title")
	social_description = data.get("social_description")
	social_image = data.get("social_image")
	published = int(data.get("published") or 0)
	if not title:
		frappe.throw("Title is required")
	if not content or not str(content).strip():
		frappe.throw("Content is required")
	if not slug:
		frappe.throw("Slug is required")
	if not re.match(r"^[a-z0-9\-]+$", slug):
		frappe.throw("Slug must contain only letters, numbers and hyphens")
	doc = frappe.new_doc("Heshly Blog Post")
	doc.title = title
	doc.slug = slug
	doc.content = _sanitize_content(content)
	doc.excerpt = excerpt
	doc.featured_image = featured_image
	doc.category = category or None
	doc.author = author
	doc.published = published
	doc.meta_title = meta_title
	doc.meta_description = meta_description
	doc.meta_keywords = meta_keywords
	doc.canonical_url = canonical_url
	doc.social_title = social_title
	doc.social_description = social_description
	doc.social_image = social_image
	# tags
	tag_list = _tags_from_payload(data)
	for tag_val in tag_list:
		# resolve to Heshly Blog Tag name (slug or tag_name); normalize slug lookup
		norm = _normalize_slug(tag_val) if isinstance(tag_val, str) else tag_val
		tag_name = frappe.db.get_value("Heshly Blog Tag", {"slug": tag_val}, "name")
		if not tag_name and norm != tag_val:
			tag_name = frappe.db.get_value("Heshly Blog Tag", {"slug": norm}, "name")
		if not tag_name:
			tag_name = frappe.db.get_value("Heshly Blog Tag", {"tag_name": tag_val}, "name")
		if not tag_name:
			# also try name directly (name == slug after normalization)
			if frappe.db.exists("Heshly Blog Tag", tag_val):
				tag_name = tag_val
			elif norm != tag_val and frappe.db.exists("Heshly Blog Tag", norm):
				tag_name = norm
		if not tag_name:
			frappe.throw(f"Tag '{tag_val}' not found")
		doc.append("tags", {"tag": tag_name})
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	return _serialize_post(doc, include_content=True)


@frappe.whitelist()
def update_post(**kwargs):
	_require_system_manager()
	data = dict(kwargs)
	if "data" in data and isinstance(data["data"], str):
		try:
			parsed = json.loads(data["data"])
			if isinstance(parsed, dict):
				data.update(parsed)
		except Exception:
			pass
	name = data.get("name")
	if not name:
		frappe.throw("name is required")
	doc = frappe.get_doc("Heshly Blog Post", name)
	# update fields if provided
	for field in ["title", "excerpt", "featured_image", "category", "meta_title", "meta_description", "meta_keywords", "canonical_url", "social_title", "social_description", "social_image"]:
		if field in data:
			setattr(doc, field, data[field])
	if "content" in data:
		doc.content = _sanitize_content(data["content"] or "")
	if "slug" in data and data["slug"] is not None:
		doc.slug = _normalize_slug(str(data["slug"] or ""))
	if "author" in data and data["author"]:
		doc.author = data["author"]
	if "published" in data:
		try:
			doc.published = int(data["published"])
		except Exception:
			pass
	if "tags" in data or "tag_list" in data or "tag" in data:
		tag_list = _tags_from_payload(data)
		doc.set("tags", [])
		for tag_val in tag_list:
			norm = _normalize_slug(tag_val) if isinstance(tag_val, str) else tag_val
			tag_name = frappe.db.get_value("Heshly Blog Tag", {"slug": tag_val}, "name")
			if not tag_name and norm != tag_val:
				tag_name = frappe.db.get_value("Heshly Blog Tag", {"slug": norm}, "name")
			if not tag_name:
				tag_name = frappe.db.get_value("Heshly Blog Tag", {"tag_name": tag_val}, "name")
			if not tag_name:
				if frappe.db.exists("Heshly Blog Tag", tag_val):
					tag_name = tag_val
				elif norm != tag_val and frappe.db.exists("Heshly Blog Tag", norm):
					tag_name = norm
			if not tag_name:
				frappe.throw(f"Tag '{tag_val}' not found")
			doc.append("tags", {"tag": tag_name})
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return _serialize_post(doc, include_content=True)


@frappe.whitelist()
def delete_post(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	frappe.delete_doc("Heshly Blog Post", name, ignore_permissions=False)
	frappe.db.commit()
	return {"success": True, "name": name}


@frappe.whitelist()
def duplicate_post(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	src = frappe.get_doc("Heshly Blog Post", name)
	base_slug = _normalize_slug(src.slug or src.title or "post")
	# generate unique slug
	candidate = f"{base_slug}-copy"
	suffix = 0
	while frappe.db.exists("Heshly Blog Post", {"slug": candidate}):
		suffix += 1
		candidate = f"{base_slug}-copy-{suffix}"
		if suffix > 100:
			candidate = f"{base_slug}-{frappe.generate_hash(length=6).lower()}"
			break
	new_title = f"{src.title} (Copy)" if src.title else "Copy"
	doc = frappe.new_doc("Heshly Blog Post")
	doc.title = new_title
	doc.slug = candidate
	doc.content = _sanitize_content(src.content)
	doc.excerpt = src.excerpt
	doc.featured_image = src.featured_image
	doc.category = src.category
	doc.author = frappe.session.user
	doc.published = 0
	doc.published_on = None
	doc.meta_title = src.meta_title
	doc.meta_description = src.meta_description
	doc.meta_keywords = src.meta_keywords
	doc.canonical_url = None
	doc.social_title = src.social_title
	doc.social_description = src.social_description
	doc.social_image = src.social_image
	# copy tags
	try:
		for row in (src.tags or []):
			doc.append("tags", {"tag": row.tag})
	except Exception:
		pass
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	return _serialize_post(doc, include_content=True)


@frappe.whitelist()
def publish(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	doc = frappe.get_doc("Heshly Blog Post", name)
	if not doc.title or not str(doc.title).strip():
		frappe.throw("Title required to publish")
	if not doc.content or not str(doc.content).strip():
		frappe.throw("Content required to publish")
	doc.published = 1
	# published_on handled by validate; ensure set
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	doc.reload()
	return _serialize_post(doc, include_content=True)


@frappe.whitelist()
def unpublish(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	doc = frappe.get_doc("Heshly Blog Post", name)
	doc.published = 0
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	doc.reload()
	return _serialize_post(doc, include_content=True)


# ---------------------------------------------------------------------------
# Categories CRUD (admin)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def list_categories(search: str | None = None):
	_require_system_manager()
	filters = {}
	rows = frappe.get_all("Heshly Blog Category", filters=filters, fields=["name", "category_name", "slug", "description", "published", "sort_order"], order_by="sort_order asc, category_name asc", limit_page_length=100)
	if search and str(search).strip():
		s = str(search).strip().lower()
		rows = [r for r in rows if s in (r.get("category_name") or "").lower() or s in (r.get("slug") or "").lower()]
	return rows


@frappe.whitelist()
def get_category(name: str):
	_require_system_manager()
	doc = frappe.get_doc("Heshly Blog Category", name)
	return {"name": doc.name, "category_name": doc.category_name, "slug": doc.slug, "description": doc.description, "published": int(doc.published or 0), "sort_order": doc.sort_order}


@frappe.whitelist()
def create_category(**kwargs):
	_require_system_manager()
	data = dict(kwargs)
	if "data" in data and isinstance(data["data"], str):
		try:
			parsed = json.loads(data["data"])
			if isinstance(parsed, dict):
				data.update(parsed)
		except Exception:
			pass
	category_name = (data.get("category_name") or data.get("name") or "").strip()
	slug = _normalize_slug(str(data.get("slug") or category_name))
	description = data.get("description")
	published = int(data.get("published") if data.get("published") is not None else 1)
	sort_order = int(data.get("sort_order") or 0)
	if not category_name:
		frappe.throw("category_name required")
	if not slug:
		frappe.throw("slug required")
	doc = frappe.new_doc("Heshly Blog Category")
	doc.category_name = category_name
	doc.slug = slug
	doc.description = description
	doc.published = published
	doc.sort_order = sort_order
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	return {"name": doc.name, "category_name": doc.category_name, "slug": doc.slug, "description": doc.description, "published": int(doc.published or 0), "sort_order": doc.sort_order}


@frappe.whitelist()
def update_category(**kwargs):
	_require_system_manager()
	data = dict(kwargs)
	if "data" in data and isinstance(data["data"], str):
		try:
			parsed = json.loads(data["data"])
			if isinstance(parsed, dict):
				data.update(parsed)
		except Exception:
			pass
	name = data.get("name")
	if not name:
		frappe.throw("name required")
	doc = frappe.get_doc("Heshly Blog Category", name)
	if "category_name" in data and data["category_name"]:
		doc.category_name = str(data["category_name"]).strip()
	if "slug" in data and data["slug"]:
		doc.slug = _normalize_slug(str(data["slug"]))
	if "description" in data:
		doc.description = data["description"]
	if "published" in data:
		doc.published = int(data["published"])
	if "sort_order" in data:
		doc.sort_order = int(data["sort_order"] or 0)
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return {"name": doc.name, "category_name": doc.category_name, "slug": doc.slug, "description": doc.description, "published": int(doc.published or 0), "sort_order": doc.sort_order}


@frappe.whitelist()
def delete_category(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	# prevent delete if posts use it
	cnt = frappe.db.count("Heshly Blog Post", {"category": name})
	if cnt and int(cnt) > 0:
		frappe.throw(f"Cannot delete category in use by {cnt} post(s)")
	frappe.delete_doc("Heshly Blog Category", name, ignore_permissions=False)
	frappe.db.commit()
	return {"success": True}


# ---------------------------------------------------------------------------
# Tags CRUD (admin)
# ---------------------------------------------------------------------------

def _serialize_tag(doc) -> dict:
	return {"name": doc.name, "tag_name": doc.tag_name, "slug": doc.slug, "description": doc.description, "color": doc.color}


@frappe.whitelist()
def list_tags(search: str | None = None):
	_require_system_manager()
	rows = frappe.get_all("Heshly Blog Tag", fields=["name", "tag_name", "slug", "description", "color"], order_by="tag_name asc", limit_page_length=100)
	if search and str(search).strip():
		s = str(search).strip().lower()
		rows = [r for r in rows if s in (r.get("tag_name") or "").lower() or s in (r.get("slug") or "").lower()]
	return rows


@frappe.whitelist()
def get_tag(name: str):
	_require_system_manager()
	doc = frappe.get_doc("Heshly Blog Tag", name)
	return _serialize_tag(doc)


@frappe.whitelist()
def create_tag(**kwargs):
	_require_system_manager()
	data = dict(kwargs)
	if "data" in data and isinstance(data["data"], str):
		try:
			parsed = json.loads(data["data"])
			if isinstance(parsed, dict):
				data.update(parsed)
		except Exception:
			pass
	tag_name = (data.get("tag_name") or data.get("name") or "").strip()
	slug = _normalize_slug(str(data.get("slug") or tag_name))
	description = data.get("description")
	color = data.get("color")
	if not tag_name:
		frappe.throw("tag_name required")
	if not slug:
		frappe.throw("slug required")
	doc = frappe.new_doc("Heshly Blog Tag")
	doc.tag_name = tag_name
	doc.slug = slug
	doc.description = description
	doc.color = color
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	return _serialize_tag(doc)


@frappe.whitelist()
def update_tag(**kwargs):
	_require_system_manager()
	data = dict(kwargs)
	if "data" in data and isinstance(data["data"], str):
		try:
			parsed = json.loads(data["data"])
			if isinstance(parsed, dict):
				data.update(parsed)
		except Exception:
			pass
	name = data.get("name")
	if not name:
		frappe.throw("name required")
	doc = frappe.get_doc("Heshly Blog Tag", name)
	if "tag_name" in data and data["tag_name"]:
		doc.tag_name = str(data["tag_name"]).strip()
	if "slug" in data and data["slug"]:
		doc.slug = _normalize_slug(str(data["slug"]))
	if "description" in data:
		doc.description = data["description"]
	if "color" in data:
		doc.color = data["color"]
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return _serialize_tag(doc)


@frappe.whitelist()
def delete_tag(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	# allow delete even if in use; child rows will remain but link breaks — we remove post tags referencing it
	# find posts with this tag
	post_tags = frappe.db.sql("SELECT parent FROM `tabHeshly Blog Post Tag` WHERE tag=%s", (name,), as_dict=True)
	frappe.delete_doc("Heshly Blog Tag", name, ignore_permissions=False)
	frappe.db.commit()
	# Note: child rows auto-removed if parent saved; but for already-saved posts, the child rows are embedded in `tabHeshly Blog Post Tag` which is deleted with doc? Actually child rows are re-saved on post save. Deleting tag does not auto-clean child rows; we clean manually
	if post_tags:
		for r in post_tags:
			try:
				frappe.db.sql("DELETE FROM `tabHeshly Blog Post Tag` WHERE parent=%s AND tag=%s", (r["parent"], name))
			except Exception:
				pass
		frappe.db.commit()
	return {"success": True}


# ---------------------------------------------------------------------------
# Media (File)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def list_media(page: int = 1, page_size: int = 20, search: str | None = None):
	_require_system_manager()
	try:
		page = int(page or 1)
		page_size = int(page_size or 20)
	except Exception:
		page, page_size = 1, 20
	page = max(1, page)
	page_size = max(1, min(100, page_size))
	# Only expose permitted File records: where file_url not null and (is_private=0 OR attached_to_doctype is null/attachment). But spec says include both attached and unattached permitted, exclude private incorrectly exposed? We return is_private flag and filter to not expose private incorrectly: return all with file_url, but mark is_private. Do NOT hide private; just include them but flag. However spec: private files are not incorrectly exposed — guest blog API does not leak private file_url? Our list_media is admin-only so private is visible to admin. We ensure filter: file_url is not null and not empty.
	filters = [["File", "file_url", "is", "set"]]
	# search
	if search and str(search).strip():
		s = str(search).strip()
		like = f"%{s}%"
		# use sql for search
		total = frappe.db.sql("SELECT COUNT(*) as c FROM tabFile WHERE file_url IS NOT NULL AND file_url != '' AND (file_name LIKE %s OR file_url LIKE %s)", (like, like), as_dict=True)
		total = int(total[0]["c"] if total else 0)
		rows = frappe.db.sql("SELECT name, file_name, file_url, is_private, file_size, attached_to_doctype, attached_to_name, folder, creation, modified FROM tabFile WHERE file_url IS NOT NULL AND file_url != '' AND (file_name LIKE %s OR file_url LIKE %s) ORDER BY modified DESC LIMIT %s OFFSET %s", (like, like, page_size, (page - 1) * page_size), as_dict=True)
		total_pages = (total + page_size - 1) // page_size if total else 1
		return {"files": rows, "total": total, "total_pages": total_pages, "page": page, "page_size": page_size}
	total = frappe.db.count("File", filters=filters)
	rows = frappe.get_all("File", filters=filters, fields=["name", "file_name", "file_url", "is_private", "file_size", "attached_to_doctype", "attached_to_name", "folder", "creation", "modified"], order_by="modified desc", limit_start=(page - 1) * page_size, limit_page_length=page_size)
	# frappe count with is set may be off; fallback
	if total is None:
		total = len(rows)
	total_pages = (int(total) + page_size - 1) // page_size if total else 1
	return {"files": rows, "total": int(total), "total_pages": total_pages, "page": page, "page_size": page_size}


@frappe.whitelist()
def delete_media(name: str):
	_require_system_manager()
	if not name:
		frappe.throw("name required")
	doc = frappe.get_doc("File", name)
	# Safety: do not delete if attached_to_doctype is set? Spec says don't delete production media during testing; but delete_media should still work for admin. We allow but log.
	frappe.delete_doc("File", name, ignore_permissions=False)
	frappe.db.commit()
	return {"success": True, "name": name}


@frappe.whitelist()
def reorder_categories(**kwargs):
	_require_system_manager()
	data = kwargs
	if "ordered_names" in data and isinstance(data["ordered_names"], str):
		try:
			import json as _json
			parsed = _json.loads(data["ordered_names"])
			if isinstance(parsed, list):
				data["ordered_names"] = parsed
		except Exception:
			pass
	ordered = data.get("ordered_names") or data.get("orderedNames") or data.get("names") or []
	if isinstance(ordered, str):
		try:
			import json as _json
			ordered = _json.loads(ordered)
		except Exception:
			ordered = []
	if not isinstance(ordered, list) or not ordered:
		frappe.throw("ordered_names required")
	# smallest compatible: update sort_order sequentially
	for idx, nm in enumerate(ordered):
		if not nm:
			continue
		try:
			frappe.db.set_value("Heshly Blog Category", nm, "sort_order", idx, update_modified=False)
		except Exception:
			continue
	frappe.db.commit()
	return {"success": True, "count": len(ordered)}


@frappe.whitelist()
def reorder_tags(**kwargs):
	_require_system_manager()
	data = kwargs
	if "ordered_names" in data and isinstance(data["ordered_names"], str):
		try:
			import json as _json
			parsed = _json.loads(data["ordered_names"])
			if isinstance(parsed, list):
				data["ordered_names"] = parsed
		except Exception:
			pass
	ordered = data.get("ordered_names") or data.get("orderedNames") or data.get("names") or []
	if isinstance(ordered, str):
		try:
			import json as _json
			ordered = _json.loads(ordered)
		except Exception:
			ordered = []
	if not isinstance(ordered, list) or not ordered:
		frappe.throw("ordered_names required")
	# Tags have no sort_order field; add one if missing via in-memory update + persist sort_order if column exists else use creation order fallback.
	# Check if sort_order column exists
	has_col = False
	try:
		has_col = bool(frappe.db.sql("SHOW COLUMNS FROM `tabHeshly Blog Tag` LIKE 'sort_order'", as_dict=True))
	except Exception:
		pass
	if has_col:
		for idx, nm in enumerate(ordered):
			if not nm:
				continue
			try:
				frappe.db.set_value("Heshly Blog Tag", nm, "sort_order", idx, update_modified=False)
			except Exception:
				continue
		frappe.db.commit()
	else:
		# No column — ordering is ephemeral; return ordered list for frontend to use (client-side order)
		frappe.db.commit()
	return {"success": True, "count": len(ordered), "persisted": has_col}

# ---------------------------------------------------------------------------
# Website Pages (WordPress-like CMS)
# ---------------------------------------------------------------------------

_ALLOWED_SECTION_TYPES = {
    "hero", "rich_text", "rich-text",
    "image_with_text", "image-with-text",
    "cards", "benefits", "testimonials",
    "faq", "cta", "gallery", "spacer", "contact", "stats",
    "content", "features", "how_it_works", "how-it-works",
}
# normalized to snake_case for storage
def _norm_section_type(t: str) -> str:
    t = (t or "").strip().lower().replace("-", "_")
    return t

def _parse_sections_value(v) -> list:
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        try:
            j = json.loads(s)
            if isinstance(j, list):
                return j
            if isinstance(j, dict):
                return [j]
            return []
        except Exception:
            return []
    return []

def _sanitize_sections(sections: list) -> list:
    out = []
    for sec in sections or []:
        if not isinstance(sec, dict):
            continue
        t = _norm_section_type(str(sec.get("type") or sec.get("section_type") or "content"))
        # allow any type but normalize; reject if not in allowed? keep but mark
        # we keep all but sanitize html fields
        nd = dict(sec)
        nd["type"] = t
        # sanitize known html fields
        for k in ("content", "html", "body", "text", "description"):
            if k in nd and isinstance(nd[k], str) and nd[k]:
                nd[k] = _sanitize_content(nd[k])
        out.append(nd)
    return out

def _serialize_page(doc, include_draft: bool = False) -> dict:
    d = {
        "name": doc.name,
        "title": doc.title,
        "route": doc.route,
        "page_type": doc.page_type,
        "content": doc.content,
        "sections": _parse_sections_value(getattr(doc, "sections", None)),
        "published": int(getattr(doc, "published", 0) or 0),
        "show_in_navigation": int(getattr(doc, "show_in_navigation", 0) or 0),
        "show_in_footer": int(getattr(doc, "show_in_footer", 0) or 0),
        "navigation_group": getattr(doc, "navigation_group", None),
        "sort_order": getattr(doc, "sort_order", None),
        "meta_title": getattr(doc, "meta_title", None),
        "meta_description": getattr(doc, "meta_description", None),
        "meta_keywords": getattr(doc, "meta_keywords", None),
        "canonical_url": getattr(doc, "canonical_url", None),
        "social_image": getattr(doc, "social_image", None),
        "creation": str(doc.creation) if getattr(doc, "creation", None) else None,
        "modified": str(doc.modified) if getattr(doc, "modified", None) else None,
    }
    if include_draft:
        d["draft_sections"] = _parse_sections_value(getattr(doc, "draft_sections", None))
        # draft mirrors for atomic publish
        d["draft_title"] = getattr(doc, "draft_title", None)
        d["draft_content"] = getattr(doc, "draft_content", None)
        d["draft_social_image"] = getattr(doc, "draft_social_image", None)
        d["draft_meta_title"] = getattr(doc, "draft_meta_title", None)
        d["draft_meta_description"] = getattr(doc, "draft_meta_description", None)
        d["draft_meta_keywords"] = getattr(doc, "draft_meta_keywords", None)
        d["draft_canonical_url"] = getattr(doc, "draft_canonical_url", None)
        # also expose canonical_url/social etc draft fallbacks for editor convenience
        # if draft_* empty, editor sees published value
    return d

def _norm_page_route(route: str) -> str:
    # reuse doctype logic
    try:
        from heshly_core.heshly_core.doctype.heshly_website_page.heshly_website_page import _norm_route as _nr
        return _nr(route)
    except Exception:
        r = (route or "").strip().lower().strip("/")
        r = re.sub(r"[^a-z0-9/\-]+", "-", r)
        r = re.sub(r"-{2,}", "-", r).strip("-/ ")
        return f"/{r}" if r else "/"

def _is_reserved_page_route(route: str) -> bool:
    try:
        from heshly_core.heshly_core.doctype.heshly_website_page.heshly_website_page import RESERVED_ROUTES
        seg = route.strip("/").split("/")[0].lower() if route != "/" else ""
        if route != "/" and seg in RESERVED_ROUTES and route.strip("/").lower() in RESERVED_ROUTES:
            return True
        # also check business_slug reserved
        try:
            from heshly_core.services.business_slug import RESERVED_SLUGS
            slug_seg = route.strip("/").split("/")[0].lower()
            if slug_seg in RESERVED_SLUGS and "/" not in route.strip("/"):
                # single segment that collides with business reserved -> but for website pages,
                # /about is not reserved, so only block if exact reserved
                if route.strip("/").lower() in RESERVED_SLUGS and route.strip("/").lower() in {"partner","login","signup","admin","blog","api","app","clients","erp","n8n"}:
                    return True
        except Exception:
            pass
        return False
    except Exception:
        return False

@frappe.whitelist()
def list_pages(search: str | None = None):
    _require_system_manager()
    rows = frappe.get_all("Heshly Website Page", fields=["name","title","route","page_type","published","show_in_navigation","sort_order","modified","creation","meta_title"], order_by="sort_order asc, route asc", limit_page_length=200)
    # enrich with sections count for admin preview
    if search and str(search).strip():
        s = str(search).strip().lower()
        rows = [r for r in rows if s in (r.get("title") or "").lower() or s in (r.get("route") or "").lower()]
    # parse draft/published sizes
    for r in rows:
        try:
            doc = frappe.get_doc("Heshly Website Page", r["name"])
            r["sections"] = _parse_sections_value(doc.sections)
            r["draft_sections"] = _parse_sections_value(doc.draft_sections)
            r["sections_count"] = len(r["sections"])
            r["draft_count"] = len(r["draft_sections"])
        except Exception:
            r["sections"] = []
            r["draft_sections"] = []
    return rows

@frappe.whitelist()
def get_page(name: str | None = None, route: str | None = None):
    _require_system_manager()
    doc = None
    if name:
        doc = frappe.get_doc("Heshly Website Page", name)
    elif route:
        nr = _norm_page_route(route)
        doc = frappe.get_doc("Heshly Website Page", {"route": nr})
        if not doc:
            # try by name == route
            try:
                doc = frappe.get_doc("Heshly Website Page", nr)
            except Exception:
                frappe.throw("Page not found")
    else:
        frappe.throw("name or route required")
    return _serialize_page(doc, include_draft=True)

@frappe.whitelist(allow_guest=True)
def get_public_page(route: str | None = None, **kwargs):
    # public: only published pages, no draft, no auth required
    r = route or kwargs.get("route") or kwargs.get("path") or ""
    # if called with slug param
    if not r and kwargs.get("slug"):
        r = kwargs.get("slug")
    # normalize: allow "about" or "/about"
    if r and not r.startswith("/"):
        r = "/" + r
    nr = _norm_page_route(r or "/")
    # Guest never sees draft
    doc = None
    try:
        doc = frappe.get_doc("Heshly Website Page", {"route": nr})
    except Exception:
        doc = None
    if not doc:
        # try name fallback
        try:
            doc = frappe.get_doc("Heshly Website Page", nr)
            if doc.route != nr:
                doc = None
        except Exception:
            doc = None
    if not doc or int(getattr(doc, "published", 0) or 0) != 1:
        return {"success": False, "not_found": True, "route": nr}
    d = _serialize_page(doc, include_draft=False)
    d["success"] = True
    return d

@frappe.whitelist()
def create_page(**kwargs):
    _require_system_manager()
    data = dict(kwargs)
    if "data" in data and isinstance(data["data"], str):
        try:
            parsed = json.loads(data["data"])
            if isinstance(parsed, dict):
                data.update(parsed)
        except Exception:
            pass
    title = (data.get("title") or "").strip()
    route = _norm_page_route(str(data.get("route") or data.get("slug") or ""))
    page_type = (data.get("page_type") or "Content").strip() or "Content"
    content = data.get("content") or ""
    # sections payload may be under sections / draft_sections / blocks
    raw_sections = data.get("draft_sections")
    if raw_sections is None:
        raw_sections = data.get("sections")
    if raw_sections is None:
        raw_sections = data.get("blocks") or []
    if isinstance(raw_sections, str):
        try:
            raw_sections = json.loads(raw_sections)
        except Exception:
            raw_sections = []
    if not isinstance(raw_sections, list):
        raw_sections = [raw_sections] if raw_sections else []
    raw_sections = _sanitize_sections(raw_sections)
    meta_title = data.get("meta_title")
    meta_description = data.get("meta_description")
    meta_keywords = data.get("meta_keywords")
    social_image = data.get("social_image")
    canonical_url = data.get("canonical_url")
    published = int(data.get("published") or 0)
    if not title:
        frappe.throw("Title required")
    if not route:
        frappe.throw("Route required")
    if _is_reserved_page_route(route):
        frappe.throw(f"Route {route} is reserved for platform use.")
    # validate content sanitize
    if content:
        content = _sanitize_content(str(content))
    doc = frappe.new_doc("Heshly Website Page")
    doc.title = title
    doc.route = route
    doc.page_type = page_type
    doc.content = content
    # draft/publish separation: draft_sections always gets payload, sections only if published
    try:
        import json as _j
        doc.draft_sections = _j.dumps(raw_sections)
        doc.sections = _j.dumps(raw_sections if published else [])
    except Exception:
        doc.draft_sections = "[]"
        doc.sections = "[]"
    doc.meta_title = meta_title
    doc.meta_description = meta_description
    doc.meta_keywords = meta_keywords
    doc.social_image = social_image
    doc.canonical_url = canonical_url
    # seed draft mirrors so editor has initial draft state
    doc.draft_title = title
    doc.draft_content = content
    doc.draft_meta_title = meta_title
    doc.draft_meta_description = meta_description
    doc.draft_meta_keywords = meta_keywords
    doc.draft_social_image = social_image
    doc.draft_canonical_url = canonical_url
    doc.published = 1 if published else 0
    # optional nav
    if "show_in_navigation" in data:
        doc.show_in_navigation = int(data["show_in_navigation"] or 0)
    if "show_in_footer" in data:
        doc.show_in_footer = int(data["show_in_footer"] or 0)
    if "navigation_group" in data:
        doc.navigation_group = data["navigation_group"]
    if "sort_order" in data and str(data["sort_order"]).strip() != "":
        try:
            doc.sort_order = int(data["sort_order"])
        except Exception:
            pass
    doc.insert(ignore_permissions=False)
    frappe.db.commit()
    return _serialize_page(doc, include_draft=True)

@frappe.whitelist()
def update_page(**kwargs):
    _require_system_manager()
    data = dict(kwargs)
    if "data" in data and isinstance(data["data"], str):
        try:
            parsed = json.loads(data["data"])
            if isinstance(parsed, dict):
                data.update(parsed)
        except Exception:
            pass
    name = data.get("name")
    if not name:
        frappe.throw("name required")
    doc = frappe.get_doc("Heshly Website Page", name)
    # Draft isolation: title and metadata go to draft_* until publish
    if "title" in data and str(data["title"]).strip():
        doc.draft_title = str(data["title"]).strip()
        # On creation, ensure live title exists; on update keep live title unchanged until publish
        if not getattr(doc, "title", None) or not str(doc.title).strip():
            doc.title = str(data["title"]).strip()
    if "route" in data and str(data["route"]).strip():
        nr = _norm_page_route(str(data["route"]))
        if _is_reserved_page_route(nr):
            frappe.throw(f"Route {nr} is reserved for platform use.")
        doc.route = nr
    if "page_type" in data and data["page_type"]:
        doc.page_type = str(data["page_type"]).strip()
    # content handled via draft_content below
    # sections handling: update draft_sections only; sections only on publish
    has_sections = "draft_sections" in data or "sections" in data or "blocks" in data
    if has_sections:
        raw = data.get("draft_sections")
        if raw is None:
            raw = data.get("sections")
        if raw is None:
            raw = data.get("blocks")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []
        if not isinstance(raw, list):
            raw = [raw] if raw else []
        raw = _sanitize_sections(raw)
        try:
            import json as _j
            doc.draft_sections = _j.dumps(raw)
            # DO NOT overwrite doc.sections unless explicitly publishing via publish_page
            # keep published sections stable until publish
        except Exception:
            pass
    # navigation_group/sort_order are not draft-isolated (admin config)
    for f in ("meta_title","meta_description","meta_keywords","social_image","canonical_url"):
        if f in data:
            setattr(doc, f"draft_{f}", data[f])
    for f in ("navigation_group",):
        if f in data:
            setattr(doc, f, data[f])
    if "content" in data:
        doc.draft_content = _sanitize_content(str(data["content"] or ""))
    if "show_in_navigation" in data:
        doc.show_in_navigation = int(data["show_in_navigation"] or 0)
    if "show_in_footer" in data:
        doc.show_in_footer = int(data["show_in_footer"] or 0)
    if "sort_order" in data and str(data["sort_order"]).strip() != "":
        try:
            doc.sort_order = int(data["sort_order"])
        except Exception:
            pass
    # published flag: if caller tries to set published=1 directly, we enforce draft->sections copy
    if "published" in data:
        want = int(data["published"] or 0)
        if want == 1 and int(doc.published or 0) == 0:
            # publishing via update: copy draft -> sections
            try:
                import json as _j
                draft = _parse_sections_value(doc.draft_sections)
                doc.sections = _j.dumps(draft)
                doc.published = 1
            except Exception:
                doc.published = 1
        elif want == 0:
            doc.published = 0
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    doc.reload()
    return _serialize_page(doc, include_draft=True)

@frappe.whitelist()
def delete_page(name: str):
    _require_system_manager()
    if not name:
        frappe.throw("name required")
    frappe.delete_doc("Heshly Website Page", name, ignore_permissions=False)
    frappe.db.commit()
    return {"success": True, "name": name}

@frappe.whitelist()
def duplicate_page(name: str):
    _require_system_manager()
    if not name:
        frappe.throw("name required")
    src = frappe.get_doc("Heshly Website Page", name)
    base_route = src.route.rstrip("/")
    # generate copy route: /about -> /about-copy, increment -2 etc
    candidate = base_route + "-copy" if base_route != "/" else "/copy"
    # ensure not reserved and not exists
    tries = 0
    cand = candidate
    while tries < 20:
        if _is_reserved_page_route(cand):
            cand = cand + "-2"
            tries += 1
            continue
        exists = frappe.db.get_value("Heshly Website Page", {"route": cand}, "name")
        if not exists:
            break
        # append -2, -3
        if cand.endswith("-copy"):
            cand = cand + "-2"
        else:
            # increment suffix
            import re as _re
            m = _re.search(r"-(\d+)$", cand)
            if m:
                n = int(m.group(1)) + 1
                cand = _re.sub(r"-(\d+)$", f"-{n}", cand)
            else:
                cand = cand + "-2"
        tries += 1
    doc = frappe.new_doc("Heshly Website Page")
    doc.title = (src.title + " (Copy)") if src.title else "Copy"
    doc.route = cand
    doc.page_type = src.page_type
    doc.content = src.content
    doc.sections = src.sections
    doc.draft_sections = src.draft_sections or src.sections
    doc.meta_title = src.meta_title
    doc.meta_description = src.meta_description
    doc.meta_keywords = src.meta_keywords
    doc.social_image = src.social_image
    doc.canonical_url = None
    doc.published = 0
    doc.show_in_navigation = 0
    doc.show_in_footer = 0
    doc.insert(ignore_permissions=False)
    frappe.db.commit()
    return _serialize_page(doc, include_draft=True)

@frappe.whitelist()
def publish_page(name: str):
    _require_system_manager()
    if not name:
        frappe.throw("name required")
    doc = frappe.get_doc("Heshly Website Page", name)
    if not doc.title or not str(doc.title).strip():
        frappe.throw("Title required to publish")
    # atomic publish: copy all draft_* -> live fields
    try:
        import json as _j
        draft = _parse_sections_value(doc.draft_sections)
        if not draft:
            draft = _parse_sections_value(doc.sections)
        draft = _sanitize_sections(draft)
        doc.sections = _j.dumps(draft)
        doc.draft_sections = _j.dumps(draft)
    except Exception:
        pass
    # copy draft title/meta/content/social to live
    if getattr(doc, "draft_title", None) and str(doc.draft_title).strip():
        doc.title = str(doc.draft_title).strip()
    if getattr(doc, "draft_content", None) is not None:
        doc.content = doc.draft_content or ""
    for f in ("meta_title","meta_description","meta_keywords","social_image","canonical_url"):
        df = getattr(doc, f"draft_{f}", None)
        if df is not None:
            setattr(doc, f, df)
    doc.published = 1
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    doc.reload()
    return _serialize_page(doc, include_draft=True)

@frappe.whitelist()
def unpublish_page(name: str):
    _require_system_manager()
    if not name:
        frappe.throw("name required")
    doc = frappe.get_doc("Heshly Website Page", name)
    doc.published = 0
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    doc.reload()
    return _serialize_page(doc, include_draft=True)
