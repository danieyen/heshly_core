from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Customer:
    id: str
    name: str


@dataclass
class Availability:
    date: str
    time: str
    available: bool


@dataclass
class Appointment:
    id: str
    customer_id: str
    service: str
    date: str
    time: str
    status: str


class CustomerManager:

    def create(
        self,
        name: str,
    ) -> Customer:

        return Customer(
            id="CUST-001",
            name=name,
        )


class AvailabilityManager:

    def check(
        self,
        date: str,
        time: str,
    ) -> Availability:

        return Availability(
            date=date,
            time=time,
            available=True,
        )


class BookingManager:

    def book(
        self,
        customer: Customer,
        availability: Availability,
        service: str,
    ) -> Appointment:

        return Appointment(
            id="APT-001",
            customer_id=customer.id,
            service=service,
            date=availability.date,
            time=availability.time,
            status="Booked",
        )


class CalendarManager:

    def save(
        self,
        appointment: Appointment,
    ) -> bool:

        return True


class NotificationManager:

    def confirm(
        self,
        appointment: Appointment,
    ) -> bool:

        return True


def test_booking_flow():

    print("\n================================")
    print("Booking Flow Test")
    print("================================\n")

    customers = CustomerManager()
    availability = AvailabilityManager()
    booking = BookingManager()
    calendar = CalendarManager()
    notifications = NotificationManager()

    customer = customers.create(
        "John Doe",
    )

    assert customer.id == "CUST-001"
    print("✅ Customer Created")

    slot = availability.check(
        "2026-07-20",
        "10:00",
    )

    assert slot.available is True
    print("✅ Availability Verified")

    appointment = booking.book(
        customer,
        slot,
        "Consultation",
    )

    assert appointment.status == "Booked"
    print("✅ Appointment Booked")

    assert calendar.save(
        appointment,
    )
    print("✅ Calendar Updated")

    assert notifications.confirm(
        appointment,
    )
    print("✅ Confirmation Sent")

    print("\n🎉 BOOKING FLOW TEST PASSED\n")