from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:
    id: str
    name: str


@dataclass
class Appointment:
    id: str
    customer_id: str
    amount: float
    status: str


@dataclass
class Payment:
    id: str
    appointment_id: str
    amount: float
    provider: str
    status: str


class AppointmentManager:

    def create(
        self,
        customer: Customer,
    ) -> Appointment:

        return Appointment(
            id="APT-001",
            customer_id=customer.id,
            amount=1500.0,
            status="Pending Payment",
        )


class PaymentGateway:

    def process(
        self,
        appointment: Appointment,
    ) -> Payment:

        return Payment(
            id="PAY-001",
            appointment_id=appointment.id,
            amount=appointment.amount,
            provider="Mock Gateway",
            status="Paid",
        )


class ReceiptService:

    def generate(
        self,
        payment: Payment,
    ) -> bool:

        return True


class NotificationService:

    def send(
        self,
        payment: Payment,
    ) -> bool:

        return True


class AnalyticsService:

    def record(
        self,
        payment: Payment,
    ) -> bool:

        return True


def test_payment_flow():

    print("\n================================")
    print("Payment Flow Test")
    print("================================\n")

    customer = Customer(
        id="CUST-001",
        name="John Doe",
    )

    appointments = AppointmentManager()

    gateway = PaymentGateway()

    receipts = ReceiptService()

    notifications = NotificationService()

    analytics = AnalyticsService()

    appointment = appointments.create(
        customer,
    )

    assert appointment.status == "Pending Payment"

    print("✅ Appointment Ready")

    payment = gateway.process(
        appointment,
    )

    assert payment.status == "Paid"

    print("✅ Payment Processed")

    appointment.status = "Confirmed"

    assert appointment.status == "Confirmed"

    print("✅ Appointment Confirmed")

    assert receipts.generate(
        payment,
    )

    print("✅ Receipt Generated")

    assert notifications.send(
        payment,
    )

    print("✅ Customer Notified")

    assert analytics.record(
        payment,
    )

    print("✅ Analytics Updated")

    print("\n🎉 PAYMENT FLOW TEST PASSED\n")