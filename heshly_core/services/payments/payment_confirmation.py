from __future__ import annotations

from datetime import datetime

from heshly_core.models.payment import (
    Invoice,
    PaymentResult,
    PaymentStatus,
)


class PaymentConfirmation:
    """
    Handles payment confirmation after a
    provider reports the payment result.
    """

    def confirm(
        self,
        invoice: Invoice,
        result: PaymentResult,
    ) -> Invoice:

        if result.success:
            invoice.status = PaymentStatus.PAID
        else:
            invoice.status = PaymentStatus.FAILED

        invoice.updated_at = datetime.utcnow()

        return invoice

    def payment_received(
        self,
        result: PaymentResult,
    ) -> bool:

        return (
            result.success
            and result.status == PaymentStatus.PAID
        )

    def should_confirm_appointment(
        self,
        invoice: Invoice,
    ) -> bool:

        return invoice.status == PaymentStatus.PAID

    def should_notify_customer(
        self,
        invoice: Invoice,
    ) -> bool:

        return invoice.status in (
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
        )

    def should_notify_business(
        self,
        invoice: Invoice,
    ) -> bool:

        return invoice.status in (
            PaymentStatus.PAID,
            PaymentStatus.FAILED,
        )