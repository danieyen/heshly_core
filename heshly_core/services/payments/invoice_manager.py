from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from heshly_core.models.payment import (
    Invoice,
    PaymentStatus,
)


class InvoiceManager:
    """
    Handles invoice lifecycle management.
    """

    def create(
        self,
        invoice: Invoice,
    ) -> Invoice:

        invoice.updated_at = datetime.utcnow()

        return invoice

    def total(
        self,
        invoice: Invoice,
    ) -> Decimal:

        return invoice.total

    def amount_paid(
        self,
        invoice: Invoice,
        payments: list[Decimal],
    ) -> Decimal:

        return sum(
            payments,
            start=Decimal("0"),
        )

    def balance(
        self,
        invoice: Invoice,
        payments: list[Decimal],
    ) -> Decimal:

        return invoice.total - self.amount_paid(
            invoice,
            payments,
        )

    def apply_payment(
        self,
        invoice: Invoice,
        payments: list[Decimal],
        payment: Decimal,
    ) -> Invoice:

        payments.append(payment)

        balance = self.balance(
            invoice,
            payments,
        )

        if balance <= Decimal("0"):
            invoice.status = PaymentStatus.PAID

        elif balance < invoice.total:
            invoice.status = PaymentStatus.PARTIALLY_PAID

        else:
            invoice.status = PaymentStatus.PENDING

        invoice.updated_at = datetime.utcnow()

        return invoice

    def mark_failed(
        self,
        invoice: Invoice,
    ) -> Invoice:

        invoice.status = PaymentStatus.FAILED

        invoice.updated_at = datetime.utcnow()

        return invoice

    def cancel(
        self,
        invoice: Invoice,
    ) -> Invoice:

        invoice.status = PaymentStatus.CANCELLED

        invoice.updated_at = datetime.utcnow()

        return invoice