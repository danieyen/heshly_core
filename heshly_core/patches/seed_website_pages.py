"""Seed static marketing pages into Heshly Website Page (idempotent)."""
import frappe


PAGES = [
    {
        "route": "/",
        "title": "Heshly — Tell Heshly what you need.",
        "page_type": "Landing",
        "meta_title": "Heshly — AI search, discovery & matching",
        "meta_description": "Find the right business or service, get answers, compare options, and take the next step — through one intelligent assistant.",
        "published": 1,
        "sections": [],
    },
    {
        "route": "/about",
        "title": "About Heshly",
        "page_type": "Content",
        "meta_title": "About Heshly",
        "meta_description": "Heshly connects people with the right businesses through AI search and matching.",
        "published": 1,
        "sections": [],
    },
    {
        "route": "/how-it-works",
        "title": "How Heshly Works",
        "page_type": "Content",
        "published": 1,
        "sections": [],
    },
    {
        "route": "/for-businesses",
        "title": "For Businesses",
        "page_type": "Content",
        "published": 1,
        "sections": [],
    },
    {
        "route": "/resources",
        "title": "Resources",
        "page_type": "Content",
        "published": 1,
        "sections": [],
    },
]

def execute():
    for p in PAGES:
        existing = frappe.db.get_value("Heshly Website Page", {"route": p["route"]}, ["name","title","route"])
        if existing:
            continue
        doc = frappe.new_doc("Heshly Website Page")
        doc.title = p["title"]
        doc.route = p["route"]
        doc.page_type = p["page_type"]
        doc.meta_title = p.get("meta_title") or p["title"]
        doc.meta_description = p.get("meta_description") or ""
        doc.published = p.get("published", 1)
        doc.content = ""
        try:
            import json
            doc.sections = json.dumps(p.get("sections") or [])
            doc.draft_sections = json.dumps(p.get("sections") or [])
        except Exception:
            pass
        try:
            doc.insert(ignore_permissions=True)
        except Exception:
            continue
    frappe.db.commit()
