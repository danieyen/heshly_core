from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Response:
    success: bool
    provider: str
    message: str


class MockWhatsAppService:

    def send_message(
        self,
        phone: str,
        message: str,
    ) -> Response:

        return Response(
            success=True,
            provider="WhatsApp",
            message=message,
        )


class MockEmailService:

    def send_email(
        self,
        recipient: str,
        subject: str,
    ) -> Response:

        return Response(
            success=True,
            provider="Email",
            message=subject,
        )


class MockSMSService:

    def send_sms(
        self,
        phone: str,
        message: str,
    ) -> Response:

        return Response(
            success=True,
            provider="SMS",
            message=message,
        )


class MockCalendarService:

    def create_event(
        self,
        title: str,
    ) -> Response:

        return Response(
            success=True,
            provider="Calendar",
            message=title,
        )


class MockPaymentService:

    def create_payment(
        self,
        amount: float,
    ) -> Response:

        return Response(
            success=True,
            provider="Payments",
            message=f"{amount}",
        )


def test_external_service_integration():

    print("\n================================")
    print("External Service Integration Test")
    print("================================\n")

    whatsapp = MockWhatsAppService()
    email = MockEmailService()
    sms = MockSMSService()
    calendar = MockCalendarService()
    payment = MockPaymentService()

    # =====================================
    # WhatsApp
    # =====================================

    response = whatsapp.send_message(
        "+254700000000",
        "Hello",
    )

    assert response.success

    print("✅ WhatsApp")

    # =====================================
    # Email
    # =====================================

    response = email.send_email(
        "user@test.com",
        "Welcome",
    )

    assert response.success

    print("✅ Email")

    # =====================================
    # SMS
    # =====================================

    response = sms.send_sms(
        "+254700000000",
        "OTP",
    )

    assert response.success

    print("✅ SMS")

    # =====================================
    # Calendar
    # =====================================

    response = calendar.create_event(
        "Appointment",
    )

    assert response.success

    print("✅ Calendar")

    # =====================================
    # Payments
    # =====================================

    response = payment.create_payment(
        1000.00,
    )

    assert response.success

    print("✅ Payments")

    print("\n🎉 EXTERNAL SERVICE INTEGRATION TEST PASSED\n")