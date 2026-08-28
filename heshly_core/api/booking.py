import frappe
from datetime import datetime, timedelta

from heshly_core.services.tenant.tenant_context import TenantContext
from heshly_core.services.calendar.calendar_integration import CalendarIntegration
from heshly_core.models.calendar import (
    AppointmentRequest,
    CalendarEvent,
    CalendarConfiguration,
    CalendarProvider,
)
from heshly_core.models.calendar_provider import ProviderConnection


def _tenant(tenant_id=None):
    context = TenantContext()

    if tenant_id:
        context.set(str(tenant_id).strip())

    try:
        return context.require()
    except RuntimeError:
        frappe.throw("Unable to resolve active tenant.")


def _provider_connection(tenant_id):
    config = CalendarConfiguration(
        provider=CalendarProvider.ERPNEXT,
        calendar_id="erpnext",
        timezone="Africa/Nairobi",
        business_name=tenant_id,
    )

    return ProviderConnection(
        configuration=config,
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
def book_appointment(
    customer_name,
    customer_phone,
    service,
    scheduled_time,
    duration_minutes=30,
    notes=None,
    tenant_id=None,
):
    tenant_id = _tenant(tenant_id)

    start = datetime.fromisoformat(
        str(scheduled_time).replace("Z", "+00:00")
    )

    duration = int(duration_minutes)

    request = AppointmentRequest(
        customer_name=customer_name,
        customer_phone=customer_phone,
        service=service,
        start=start,
        duration_minutes=duration,
        notes=notes,
    )

    appointments = frappe.get_all(
        "Appointment",
        filters={
            "custom_heshly_tenant_id": tenant_id,
            "scheduled_time": [
                ">=",
                start.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                ),
            ],
            "status": [
                "not in",
                ["Cancelled", "Completed"],
            ],
        },
        fields=[
            "name",
            "scheduled_time",
            "customer_name",
            "customer_phone_number",
            "customer_details",
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
                end=(
                    appointment.scheduled_time
                    + timedelta(minutes=duration)
                ),
                customer_name=appointment.customer_name,
                customer_phone=appointment.customer_phone_number,
                notes=appointment.customer_details,
            )
        )

    calendar = CalendarIntegration()

    # Connect the ERPNext provider for this tenant.
    calendar.connect(
        _provider_connection(tenant_id)
    )

    result = calendar.book(
        request=request,
        events=events,
    )

    return {
        "success": result.success,
        "tenant_id": tenant_id,
        "service": service,
        "scheduled_time": start.isoformat(),
        "appointment_id": (
            result.appointment.appointment_id
            if result.appointment
            else None
        ),
        "status": (
            result.appointment.status.value
            if (
                result.appointment
                and result.appointment.status
            )
            else None
        ),
        "message": result.response,
    }
