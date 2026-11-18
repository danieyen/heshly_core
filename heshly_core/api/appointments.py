import frappe

from heshly_core.services.tenant.tenant_context import TenantContext


def _tenant():
    try:
        return TenantContext().require()
    except RuntimeError:
        frappe.throw("Unable to resolve active tenant.")


def _appointment_fields():
    return [
        "name",
        "scheduled_time",
        "status",
        "created_through_portal",
        "customer_name",
        "customer_phone_number",
        "customer_email",
        "customer_details",
        "calendar_event",
        "custom_heshly_tenant_id",
        "creation",
        "modified",
    ]


def _serialize(row):
    return {
        "id": row.name,
        "name": row.name,
        "scheduled_time": row.scheduled_time,
        "status": row.status,
        "created_through_portal": bool(
            row.created_through_portal
        ),
        "customer_name": row.customer_name,
        "customer_phone": row.customer_phone_number,
        "customer_email": row.customer_email,
        "customer_details": row.customer_details,
        "calendar_event": row.calendar_event,
        "created_at": row.creation,
        "updated_at": row.modified,
    }


@frappe.whitelist()
def list(
    status=None,
    limit=50,
    offset=0,
):
    tenant_id = _tenant()

    limit = min(int(limit or 50), 100)
    offset = max(int(offset or 0), 0)

    filters = {
        "custom_heshly_tenant_id": tenant_id,
    }

    if status:
        filters["status"] = status

    appointments = frappe.get_all(
        "Appointment",
        filters=filters,
        fields=_appointment_fields(),
        order_by="scheduled_time asc",
        limit_start=offset,
        limit_page_length=limit,
    )

    total = frappe.db.count(
        "Appointment",
        filters=filters,
    )

    return {
        "appointments": [
            _serialize(row)
            for row in appointments
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@frappe.whitelist()
def get(appointment_id):
    tenant_id = _tenant()

    appointment = frappe.get_doc(
        "Appointment",
        appointment_id,
    )

    if appointment.custom_heshly_tenant_id != tenant_id:
        frappe.throw(
            "Appointment does not belong to the active tenant.",
            frappe.PermissionError,
        )

    return _serialize(appointment)


@frappe.whitelist(methods=["POST"])
def cancel(appointment_id):
    tenant_id = _tenant()

    appointment = frappe.get_doc(
        "Appointment",
        appointment_id,
    )

    if appointment.custom_heshly_tenant_id != tenant_id:
        frappe.throw(
            "Appointment does not belong to the active tenant.",
            frappe.PermissionError,
        )

    if appointment.status == "Cancelled":
        return {
            "success": True,
            "message": "Appointment is already cancelled.",
            "appointment": _serialize(appointment),
        }

    appointment.status = "Cancelled"
    appointment.save(ignore_permissions=True)

    if appointment.calendar_event:
        event = frappe.get_doc(
            "Event",
            appointment.calendar_event,
        )

        event_tenant_id = event.get("custom_heshly_tenant_id")

        # Legacy Events may have been created before tenant tagging
        # was added. Since the Appointment has already been verified
        # to belong to the active tenant, safely backfill the Event.
        if not event_tenant_id:
            event.custom_heshly_tenant_id = tenant_id

        elif event_tenant_id != tenant_id:
            frappe.throw(
                "Calendar event does not belong to the active tenant.",
                frappe.PermissionError,
            )

        event.status = "Cancelled"
        event.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "message": "Appointment cancelled.",
        "appointment": _serialize(appointment),
    }
