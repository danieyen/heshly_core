import frappe

from heshly_core.services.calendar.providers.erpnext_provider import (
    ERPNextCalendarProvider,
)
from heshly_core.services.whatsapp.conversation_orchestrator import (
    WhatsAppConversationOrchestrator,
)


def test_provider_connection_contains_tenant():
    orchestrator = WhatsAppConversationOrchestrator()

    connection = orchestrator._provider_connection("heshly")

    assert connection.configuration.tenant_id == "heshly"
    # business_name is display-only and must not be used as tenant identifier
    assert connection.configuration.business_name == ""


def test_cross_tenant_appointment_is_blocked():
    orchestrator = WhatsAppConversationOrchestrator()

    provider = ERPNextCalendarProvider()

    connection = orchestrator._provider_connection("different-tenant")
    provider.connect(connection)

    result = provider.delete_event(
        "APMT-Tenant Safe Test-0004"
    )

    assert result.success is False
    assert "does not belong to the active tenant" in result.message


def test_tenant_tagged_booking_persists():
    appointment = frappe.get_doc(
        "Appointment",
        "APMT-Tenant Safe Test-0004",
    )

    assert appointment.custom_heshly_tenant_id == "heshly"

    event = frappe.get_doc(
        "Event",
        appointment.calendar_event,
    )

    assert event.custom_heshly_tenant_id == "heshly"
    assert appointment.calendar_event == event.name
