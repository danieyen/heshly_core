import frappe


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def get_pending(business_id=None, limit=50):

    filters = {
        "status": "pending",
        "scheduled_for": ["<=", frappe.utils.now_datetime()],
    }

    if business_id:
        filters["business_id"] = business_id

    follow_ups = frappe.get_all(
        "Follow Up",
        filters=filters,
        fields=[
            "name",
            "follow_up_id",
            "business_id",
            "related_type",
            "related_id",
            "follow_up_type",
            "scheduled_for",
            "subject",
            "description",
            "assigned_to",
            "status",
            "completed_at",
        ],
        order_by="scheduled_for asc",
        limit_page_length=int(limit),
    )

    return {
        "success": True,
        "count": len(follow_ups),
        "follow_ups": follow_ups,
    }


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def process_pending(business_id=None, limit=50):

    filters = {
        "status": "pending",
        "scheduled_for": ["<=", frappe.utils.now_datetime()],
    }

    if business_id:
        filters["business_id"] = business_id

    follow_ups = frappe.get_all(
        "Follow Up",
        filters=filters,
        fields=[
            "name",
            "follow_up_id",
            "business_id",
            "related_type",
            "related_id",
            "follow_up_type",
            "scheduled_for",
            "subject",
            "description",
            "assigned_to",
            "status",
            "completed_at",
        ],
        order_by="scheduled_for asc",
        limit_page_length=int(limit),
    )

    processed = []

    for follow_up in follow_ups:

        # For now, mark the follow-up as scheduled/processed.
        # Actual WhatsApp/email/call execution can be added next.
        frappe.db.set_value(
            "Follow Up",
            follow_up["name"],
            "status",
            "scheduled",
        )

        processed.append(follow_up["follow_up_id"])

    frappe.db.commit()

    return {
        "success": True,
        "count": len(processed),
        "processed": processed,
    }
