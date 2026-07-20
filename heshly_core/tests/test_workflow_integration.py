from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:
    id: str
    name: str


@dataclass
class Appointment:
    customer_id: str
    service: str
    status: str


class CRM:

    def create_customer(self, name: str) -> Customer:

        return Customer(
            id="CUST-001",
            name=name,
        )


class Calendar:

    def book(
        self,
        customer: Customer,
        service: str,
    ) -> Appointment:

        return Appointment(
            customer_id=customer.id,
            service=service,
            status="Booked",
        )


class Notification:

    def send_confirmation(
        self,
        customer: Customer,
    ) -> bool:

        return True


class Analytics:

    def record(
        self,
        appointment: Appointment,
    ) -> bool:

        return True


class WorkflowEngine:

    def __init__(self):

        self.crm = CRM()

        self.calendar = Calendar()

        self.notifications = Notification()

        self.analytics = Analytics()

    def execute(
        self,
        customer_name: str,
        service: str,
    ):

        customer = self.crm.create_customer(
            customer_name,
        )

        appointment = self.calendar.book(
            customer,
            service,
        )

        notified = self.notifications.send_confirmation(
            customer,
        )

        tracked = self.analytics.record(
            appointment,
        )

        return (
            customer,
            appointment,
            notified,
            tracked,
        )


def test_workflow_integration():

    print("\n================================")
    print("Workflow Integration Test")
    print("================================\n")

    workflow = WorkflowEngine()

    customer, appointment, notified, tracked = workflow.execute(
        "John Doe",
        "Consultation",
    )

    assert customer.id == "CUST-001"

    print("✅ CRM")

    assert appointment.status == "Booked"

    print("✅ Calendar")

    assert notified is True

    print("✅ Notifications")

    assert tracked is True

    print("✅ Analytics")

    assert appointment.customer_id == customer.id

    print("✅ Cross-module workflow")

    print("\n🎉 WORKFLOW INTEGRATION TEST PASSED\n")