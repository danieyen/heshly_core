from __future__ import annotations

import frappe

from heshly_core.models.business_knowledge_profile import BusinessKnowledgeProfile
from heshly_core.services.ai.tenant_ai_manager import TenantAIManager


def _require_business():
    """Return the authenticated user's active Business Account."""

    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw("Authentication required.", frappe.PermissionError)

    business_id = frappe.session.data.get("heshly_business_id")

    if not business_id:
        frappe.throw("Business session not found.", frappe.PermissionError)

    business = frappe.db.get_value(
        "Business Account",
        {
            "business_id": business_id,
            "status": "Active",
        },
        [
            "business_id",
            "business_name",
            "tenant_id",
            "industry",
            "timezone",
            "currency",
        ],
        as_dict=True,
    )

    if not business:
        frappe.throw("Business account not found.", frappe.DoesNotExistError)

    membership = frappe.db.get_value(
        "User Business Membership",
        {
            "user": frappe.session.user,
            "business_id": business.business_id,
            "tenant_id": business.tenant_id,
            "active": 1,
        },
        "name",
    )

    if not membership:
        frappe.throw(
            "You do not have access to this business.",
            frappe.PermissionError,
        )

    return business


def _clean_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    return [
        line.strip()
        for line in str(value).splitlines()
        if line.strip()
    ]


@frappe.whitelist()
def get_my_business_knowledge():
    """Return knowledge belonging to the authenticated business."""

    business = _require_business()

    manager = TenantAIManager()
    knowledge = manager.knowledge(business.tenant_id)

    if knowledge is None:
        return {
            "success": True,
            "tenant_id": business.tenant_id,
            "knowledge": {
                "business_name": business.business_name or "",
                "industry": business.industry or "",
                "description": "",
                "services": [],
                "products": [],
                "faqs": [],
                "policies": [],
            },
        }

    return {
        "success": True,
        "tenant_id": business.tenant_id,
        "knowledge": {
            "business_name": knowledge.business_name,
            "industry": knowledge.industry,
            "description": knowledge.description,
            "services": knowledge.services,
            "products": knowledge.products,
            "faqs": knowledge.faqs,
            "policies": knowledge.policies,
        },
    }


@frappe.whitelist()
def update_my_business_knowledge(
    description: str = "",
    industry: str = "",
    services=None,
    products=None,
    faqs=None,
    policies=None,
):
    """Save knowledge for the authenticated business only."""

    business = _require_business()

    knowledge = BusinessKnowledgeProfile(
        profile_id=business.tenant_id,
        tenant_id=business.tenant_id,
        business_name=business.business_name or "",
        industry=(industry or business.industry or "").strip(),
        description=(description or "").strip(),
        services=_clean_list(services),
        products=_clean_list(products),
        faqs=_clean_list(faqs),
        policies=_clean_list(policies),
    )

    manager = TenantAIManager()
    manager.save_knowledge(knowledge)

    return {
        "success": True,
        "tenant_id": business.tenant_id,
        "knowledge": {
            "business_name": knowledge.business_name,
            "industry": knowledge.industry,
            "description": knowledge.description,
            "services": knowledge.services,
            "products": knowledge.products,
            "faqs": knowledge.faqs,
            "policies": knowledge.policies,
        },
    }
