from __future__ import annotations

from datetime import datetime

from heshly_core.models.payment import (
    Invoice,
    PaymentStatus,
    RefundRequest,
    RefundResult,
)


class RefundManager:
    """
    Handles refund business logic.
    """

    def create_request(
        self,
        request: RefundRequest,
    ) -> RefundRequest:
        """
        Prepare a refund request.
        """
        return request

    def can_refund(
        self,
        invoice: Invoice,
    ) -> bool:
        """
        Determine whether an invoice
        is eligible for refund.
        """
        return invoice.status == PaymentStatus.PAID

    def apply_refund(
        self,
        invoice: Invoice,
        result: RefundResult,
    ) -> Invoice:
        """
        Update invoice after a refund.
        """

        if result.success:
            invoice.status = PaymentStatus.REFUNDED

        invoice.updated_at = datetime.utcnow()

        return invoice

    def refund_completed(
        self,
        result: RefundResult,
    ) -> bool:

        return result.success

    def should_notify_customer(
        self,
        result: RefundResult,
    ) -> bool:

        return result.success

    def should_notify_business(
        self,
        result: RefundResult,
    ) -> bool:

        return True