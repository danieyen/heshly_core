from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:
    id: str
    name: str


@dataclass
class Appointment:
    id: str
    status: str


@dataclass
class Payment:
    id: str
    amount: float
    paid: bool


class CustomerJourney:

    def register(
        self,
        name: str,
    ) -> Customer:

        return Customer(
            id="CUST-001",
            name=name,
        )

    def book(
        self,
        customer: Customer,
    ) -> Appointment:

        return Appointment(
            id="APT-001",
            status="Booked",
        )

    def pay(
        self,
        appointment: Appointment,
    ) -> Payment:

        appointment.status = "Confirmed"

        return Payment(
            id="PAY-001",
            amount=1500.0,
            paid=True,
        )

    def notify(
        self,
        customer: Customer,
    ) -> bool:

        return True

    def complete(
        self,
        appointment: Appointment,
    ) -> bool:

        appointment.status = "Completed"

        return True

    def feedback(
        self,
        customer: Customer,
    ) -> int:

        return 5


def test_customer_journey():

    print("\n================================")
    print("Customer Journey Test")
    print("================================\n")

    flow = CustomerJourney()

    customer = flow.register(
        "John Doe",
    )

    assert customer.id == "CUST-001"
    print("✅ Customer Registered")

    appointment = flow.book(
        customer,
    )

    assert appointment.status == "Booked"
    print("✅ Appointment Booked")

    payment = flow.pay(
        appointment,
    )

    assert payment.paid
    assert appointment.status == "Confirmed"
    print("✅ Payment Completed")

    assert flow.notify(customer)
    print("✅ Notification Sent")

    assert flow.complete(
        appointment,
    )

    assert appointment.status == "Completed"
    print("✅ Service Completed")

    rating = flow.feedback(
        customer,
    )

    assert rating == 5
    print("✅ Feedback Captured")

    print("\n🎉 CUSTOMER JOURNEY TEST PASSED\n")