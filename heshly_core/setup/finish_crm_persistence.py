import frappe


def execute():
    frappe.set_user("Administrator")

    module = frappe.db.get_value(
        "Module Def",
        {"app_name": "heshly_core"},
        "name",
    )

    if not module:
        raise RuntimeError("No Module Def found for heshly_core")

    doctypes = {
        "Heshly Activity": [
            ("activity_id", "Data", "Activity ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("activity_type", "Data", "Activity Type", 1),
            ("subject", "Data", "Subject", 1),
            ("description", "Text Editor", "Description", 0),
            ("assigned_to", "Data", "Assigned To", 0),
            ("priority", "Data", "Priority", 0),
            ("status", "Data", "Status", 0),
            ("performed_by", "Data", "Performed By", 0),
            ("performed_at", "Datetime", "Performed At", 0),
        ],

        "Heshly Task": [
            ("task_id", "Data", "Task ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("title", "Data", "Title", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("assigned_to", "Data", "Assigned To", 0),
            ("priority", "Data", "Priority", 0),
            ("status", "Data", "Status", 0),
            ("due_date", "Datetime", "Due Date", 0),
            ("completed_at", "Datetime", "Completed At", 0),
        ],

        "Heshly Note": [
            ("note_id", "Data", "Note ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("title", "Data", "Title", 1),
            ("content", "Text Editor", "Content", 1),
            ("created_by", "Data", "Created By", 0),
        ],

        "Heshly Call": [
            ("call_id", "Data", "Call ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("direction", "Data", "Direction", 1),
            ("phone_number", "Data", "Phone Number", 1),
            ("duration_seconds", "Int", "Duration Seconds", 0),
            ("outcome", "Data", "Outcome", 0),
            ("notes", "Text Editor", "Notes", 0),
            ("logged_by", "Data", "Logged By", 0),
        ],

        "Heshly Email Activity": [
            ("email_id", "Data", "Email ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("direction", "Data", "Direction", 1),
            ("sender", "Data", "Sender", 1),
            ("recipient", "Data", "Recipient", 1),
            ("subject", "Data", "Subject", 1),
            ("body", "Text Editor", "Body", 0),
            ("status", "Data", "Status", 0),
            ("logged_by", "Data", "Logged By", 0),
        ],

        "Heshly WhatsApp Activity": [
            ("activity_id", "Data", "Activity ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("message_id", "Data", "Message ID", 1),
            ("direction", "Data", "Direction", 1),
            ("phone_number", "Data", "Phone Number", 1),
            ("message", "Text Editor", "Message", 1),
            ("status", "Data", "Status", 1),
            ("logged_by", "Data", "Logged By", 0),
        ],

        "Heshly Follow Up": [
            ("follow_up_id", "Data", "Follow Up ID", 1),
            ("tenant_id", "Data", "Tenant ID", 1),
            ("business_id", "Data", "Business ID", 1),
            ("related_type", "Data", "Related Type", 1),
            ("related_id", "Data", "Related ID", 1),
            ("follow_up_type", "Data", "Follow Up Type", 1),
            ("scheduled_for", "Datetime", "Scheduled For", 1),
            ("subject", "Data", "Subject", 1),
            ("description", "Text Editor", "Description", 0),
            ("assigned_to", "Data", "Assigned To", 0),
            ("status", "Data", "Status", 0),
            ("completed_at", "Datetime", "Completed At", 0),
        ],
    }

    for doctype_name, fields in doctypes.items():

        if frappe.db.exists("DocType", doctype_name):
            print(f"EXISTS: {doctype_name}")
            continue

        doc = frappe.new_doc("DocType")
        doc.name = doctype_name
        doc.module = module
        doc.custom = 1
        doc.istable = 0
        doc.track_changes = 1

        for fieldname, fieldtype, label, reqd in fields:
            df = doc.append("fields", {})
            df.fieldname = fieldname
            df.fieldtype = fieldtype
            df.label = label
            df.reqd = reqd

        doc.insert(
            ignore_permissions=True,
            ignore_links=True,
        )

        print(f"CREATED: {doctype_name}")

    frappe.db.commit()
    frappe.clear_cache()

    print("")
    print("=== CRM PERSISTENCE DOCTYPES ===")
    for name in doctypes:
        print(
            f"{name}: "
            f"{'OK' if frappe.db.exists('DocType', name) else 'MISSING'}"
        )

    print(f"MODULE: {module}")
