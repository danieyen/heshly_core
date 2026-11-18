from __future__ import annotations

import frappe


@frappe.whitelist()
def get_services():
    """
    Return the services belonging to the currently
    authenticated Heshly business.
    """

    business_id = frappe.session.data.get(
        "heshly_business_id"
    )

    if not business_id:
        frappe.throw(
            "Not authenticated.",
            frappe.AuthenticationError,
        )

    business = frappe.get_doc(
        "Business Account",
        business_id,
    )

    items = frappe.get_all(
        "Item",
        filters={
            "heshly_business_account": business.name,
            "is_stock_item": 0,
            "disabled": 0,
        },
        fields=[
            "name",
            "item_name",
            "description",
            "item_group",
            "standard_rate",
            "image",
        ],
        order_by="item_name asc",
    )

    return {
        "business_id": business.business_id,
        "business_name": business.business_name,
        "tenant_id": business.tenant_id,
        "services": items,
    }
