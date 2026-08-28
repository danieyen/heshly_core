import frappe
from datetime import datetime, date, time, timedelta

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.calendar.calendar_integration import CalendarIntegration
from heshly_core.models.calendar import AvailabilityRequest, CalendarEvent


def _tenant():
    try:
        return TenantContext().require()
    except RuntimeError:
        frappe.throw("Unable to resolve active tenant.")


@frappe.whitelist(allow_guest=True, methods=["POST"])
def check_availability(
    service,
    preferred_date,
    duration_minutes=30,
    tenant_id=None,
):
    if tenant_id:
        TenantContext().set(str(tenant_id).strip())

    tenant_id = _tenant()

    requested_date = date.fromisoformat(str(preferred_date))
    duration = int(duration_minutes)

    request = AvailabilityRequest(
        service=service,
        preferred_date=requested_date,
        duration_minutes=duration,
    )

    working_start = datetime.combine(
        requested_date,
        time(9, 0),
    )

    working_end = datetime.combine(
        requested_date,
        time(17, 0),
    )

    appointments = frappe.get_all(
        "Appointment",
        filters={
            "custom_heshly_tenant_id": tenant_id,
            "scheduled_time": [
                ">=",
                working_start,
            ],
        },
        fields=[
            "name",
            "scheduled_time",
            "status",
        ],
    )

    events = []

    for appointment in appointments:
        if not appointment.scheduled_time:
            continue

        events.append(
            CalendarEvent(
                event_id=appointment.name,
                title="Appointment",
                start=appointment.scheduled_time,
                end=appointment.scheduled_time + timedelta(minutes=duration),
            )
        )

    result = CalendarIntegration().check_availability(
        request=request,
        events=events,
        working_start=working_start,
        working_end=working_end,
    )

    return {
        "success": True,
        "tenant_id": tenant_id,
        "service": service,
        "preferred_date": str(requested_date),
        "available": result.available,
        "slots": [
            {
                "start": slot.start.isoformat(),
                "end": slot.end.isoformat(),
                "available": slot.available,
            }
            for slot in result.slots
        ],
    }
