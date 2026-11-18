from __future__ import annotations

from heshly_core.models.calendar import CalendarEvent

from heshly_core.models.calendar_provider import (
    CalendarProviderStatus,
    ProviderAppointmentResult,
    ProviderConnection,
    ProviderEventQuery,
    ProviderEventsResult,
    ProviderHealth,
)

from heshly_core.services.calendar.providers.provider_interface import (
    CalendarProviderInterface,
)


class ERPNextCalendarProvider(CalendarProviderInterface):
    """
    ERPNext-backed calendar provider.

    Uses ERPNext Event + Appointment DocTypes.
    """

    def __init__(self) -> None:
        self._connection: ProviderConnection | None = None

    def connect(
        self,
        connection: ProviderConnection,
    ) -> bool:
        self._connection = connection
        return True

    def _ensure_connected(self) -> None:
        if self._connection is None:
            raise RuntimeError(
                "ERPNext calendar provider is not connected."
            )

    def disconnect(self) -> None:
        self._connection = None

    def _tenant_id(self) -> str:
        self._ensure_connected()

        tenant_id = (
            self._connection.configuration.tenant_id
            if self._connection
            else None
        )

        if not tenant_id:
            raise RuntimeError(
                "Calendar provider connection has no tenant ID."
            )

        return tenant_id

    def health(self) -> ProviderHealth:
        status = (
            CalendarProviderStatus.AVAILABLE
            if self._connection
            else CalendarProviderStatus.UNAVAILABLE
        )

        return ProviderHealth(
            status=status,
            provider="ERPNext",
            message=(
                "Connected"
                if self._connection
                else "Not connected"
            ),
        )

    def get_events(
        self,
        query: ProviderEventQuery,
    ) -> ProviderEventsResult:

        self._ensure_connected()

        import frappe

        tenant_id = self._tenant_id()

        events = frappe.get_all(
            "Event",
            filters=[
                ["Event", "starts_on", ">=", query.start],
                ["Event", "starts_on", "<=", query.end],
                [
                    "Event",
                    "custom_heshly_tenant_id",
                    "=",
                    tenant_id,
                ],
            ],
            fields=[
                "name",
                "subject",
                "starts_on",
                "ends_on",
                "status",
                "description",
                "custom_heshly_tenant_id",
            ],
            order_by="starts_on asc",
        )

        calendar_events = [
            CalendarEvent(
                event_id=row.name,
                title=row.subject,
                start=row.starts_on,
                end=row.ends_on or row.starts_on,
                notes=row.description,
            )
            for row in events
        ]

        return ProviderEventsResult(
            success=True,
            events=calendar_events,
            message=f"{len(calendar_events)} event(s) found.",
        )

    def create_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        self._ensure_connected()

        import frappe

        try:
            # -------------------------------------------------
            # 1. Create ERPNext Event
            # -------------------------------------------------

            tenant_id = self._tenant_id()

            erp_event = frappe.get_doc({
                "doctype": "Event",
                "subject": event.title,
                "event_type": "Private",
                "event_category": "Meeting",
                "starts_on": event.start,
                "ends_on": event.end,
                "status": "Open",
                "description": event.notes or "",
                "custom_heshly_tenant_id": tenant_id,
            })

            erp_event.insert(
                ignore_permissions=True
            )

            # -------------------------------------------------
            # 2. Create ERPNext Appointment
            # -------------------------------------------------

            appointment = frappe.get_doc({
                "doctype": "Appointment",
                "scheduled_time": event.start,
                "status": "Open",
                "customer_name": event.customer_name or "Customer",
                "customer_phone_number": event.customer_phone or "",
                "customer_email": "no-reply@heshly.com",
                "customer_details": event.notes or "",
                "calendar_event": erp_event.name,
                "custom_heshly_tenant_id": tenant_id,
            })

            appointment.insert(
                ignore_permissions=True
            )

            frappe.db.commit()

            return ProviderAppointmentResult(
                success=True,
                event_id=appointment.name,
                message=(
                    f"Appointment {appointment.name} created "
                    f"with calendar event {erp_event.name}."
                ),
            )

        except Exception as exc:
            frappe.db.rollback()

            frappe.log_error(
                title="Heshly ERPNext Calendar Provider Error",
                message=frappe.get_traceback(),
            )

            return ProviderAppointmentResult(
                success=False,
                event_id=None,
                message=str(exc),
            )

    def update_event(
        self,
        event: CalendarEvent,
    ) -> ProviderAppointmentResult:

        self._ensure_connected()

        import frappe

        try:
            tenant_id = self._tenant_id()

            appointment_name = event.event_id

            appointment = frappe.get_doc(
                "Appointment",
                appointment_name,
            )

            if appointment.custom_heshly_tenant_id != tenant_id:
                raise PermissionError(
                    "Appointment does not belong to the active tenant."
                )

            appointment.scheduled_time = event.start
            appointment.customer_name = (
                event.customer_name or appointment.customer_name
            )

            if event.customer_phone:
                appointment.customer_phone_number = (
                    event.customer_phone
                )

            if event.notes:
                appointment.customer_details = event.notes

            appointment.save(
                ignore_permissions=True
            )

            if appointment.calendar_event:
                erp_event = frappe.get_doc(
                    "Event",
                    appointment.calendar_event,
                )

                if erp_event.custom_heshly_tenant_id != tenant_id:
                    raise PermissionError(
                        "Calendar event does not belong to the active tenant."
                    )

                erp_event.subject = event.title
                erp_event.starts_on = event.start
                erp_event.ends_on = event.end
                erp_event.description = event.notes or ""

                erp_event.save(
                    ignore_permissions=True
                )

            frappe.db.commit()

            return ProviderAppointmentResult(
                success=True,
                event_id=appointment.name,
                message=(
                    f"Appointment {appointment.name} updated."
                ),
            )

        except Exception as exc:
            frappe.db.rollback()

            frappe.log_error(
                title="Heshly ERPNext Calendar Update Error",
                message=frappe.get_traceback(),
            )

            return ProviderAppointmentResult(
                success=False,
                event_id=event.event_id,
                message=str(exc),
            )

    def delete_event(
        self,
        event_id: str,
    ) -> ProviderAppointmentResult:

        self._ensure_connected()

        import frappe

        try:
            tenant_id = self._tenant_id()

            appointment = frappe.get_doc(
                "Appointment",
                event_id,
            )

            if appointment.custom_heshly_tenant_id != tenant_id:
                raise PermissionError(
                    "Appointment does not belong to the active tenant."
                )

            calendar_event_name = (
                appointment.calendar_event
            )

            # Cancel rather than physically deleting
            # the appointment.
            appointment.status = "Cancelled"
            appointment.save(
                ignore_permissions=True
            )

            if calendar_event_name:
                erp_event = frappe.get_doc(
                    "Event",
                    calendar_event_name,
                )

                event_tenant_id = erp_event.get(
                    "custom_heshly_tenant_id"
                )

                # Legacy Events may have been created before tenant
                # tagging was added. The Appointment has already been
                # verified for this tenant, so safely backfill it.
                if not event_tenant_id:
                    erp_event.custom_heshly_tenant_id = tenant_id

                elif event_tenant_id != tenant_id:
                    raise PermissionError(
                        "Calendar event does not belong to the active tenant."
                    )

                erp_event.status = "Cancelled"
                erp_event.save(
                    ignore_permissions=True
                )

            frappe.db.commit()

            return ProviderAppointmentResult(
                success=True,
                event_id=appointment.name,
                message=(
                    f"Appointment {appointment.name} cancelled."
                ),
            )

        except Exception as exc:
            frappe.db.rollback()

            frappe.log_error(
                title="Heshly ERPNext Calendar Delete Error",
                message=frappe.get_traceback(),
            )

            return ProviderAppointmentResult(
                success=False,
                event_id=event_id,
                message=str(exc),
            )

