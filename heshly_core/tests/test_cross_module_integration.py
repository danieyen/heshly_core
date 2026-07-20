from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:
    id: str
    name: str


@dataclass
class Lead:
    id: str
    customer_id: str


@dataclass
class Appointment:
    id: str
    customer_id: str
    status: str


@dataclass
class Payment:
    id: str
    appointment_id: str
    amount: float


class CRMModule:

    def create_customer(self, name: str):

        return Customer(
            id="CUST-001",
            name=name,
        )

    def create_lead(self, customer):

        return Lead(
            id="LEAD-001",
            customer_id=customer.id,
        )


class CalendarModule:

    def book(self, customer):

        return Appointment(
            id="APT-001",
            customer_id=customer.id,
            status="Booked",
        )


class PaymentModule:

    def pay(self, appointment):

        return Payment(
            id="PAY-001",
            appointment_id=appointment.id,
            amount=1500.0,
        )


class AnalyticsModule:

    def record(self, payment):

        return True


class NotificationModule:

    def notify(self, customer):

        return True


def test_cross_module_integration():

    print("\n================================")
    print("Cross Module Integration Test")
    print("================================\n")

    crm = CRMModule()
    calendar = CalendarModule()
    payments = PaymentModule()
    analytics = AnalyticsModule()
    notifications = NotificationModule()

    customer = crm.create_customer(
        "John Doe",
    )

    lead = crm.create_lead(
        customer,
    )

    appointment = calendar.book(
        customer,
    )

    payment = payments.pay(
        appointment,
    )

    analytics_ok = analytics.record(
        payment,
    )

    notification_ok = notifications.notify(
        customer,
    )

    assert customer.id == lead.customer_id
    print("✅ CRM → Lead")

    assert appointment.customer_id == customer.id
    print("✅ CRM → Calendar")

    assert payment.appointment_id == appointment.id
    print("✅ Calendar → Payments")

    assert analytics_ok is True
    print("✅ Payments → Analytics")

    assert notification_ok is True
    print("✅ Notifications")

    print("\n🎉 CROSS MODULE INTEGRATION TEST PASSED\n")