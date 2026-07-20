from __future__ import annotations

from heshly_core.models.payment import (
    PaymentStatus,
)


class PaymentConversationFlow:
    """
    Controls the conversational flow for
    payment-related interactions.
    """

    def request_payment(self) -> str:
        """
        Initial payment request.
        """
        return (
            "Your payment is ready. "
            "Please complete it using the payment link provided."
        )

    def payment_pending(self) -> str:
        """
        Waiting for customer payment.
        """
        return (
            "We're waiting for your payment confirmation."
        )

    def payment_received(self) -> str:
        """
        Successful payment.
        """
        return (
            "Thank you! Your payment has been received successfully."
        )

    def payment_failed(self) -> str:
        """
        Failed payment.
        """
        return (
            "Your payment could not be completed. "
            "Please try again or choose another payment method."
        )

    def refund_processed(self) -> str:
        """
        Successful refund.
        """
        return (
            "Your refund has been processed successfully."
        )

    def next_step(
        self,
        status: PaymentStatus,
    ) -> str:
        """
        Determine the next conversation
        based on payment status.
        """

        if status == PaymentStatus.PENDING:
            return self.payment_pending()

        if status == PaymentStatus.PAID:
            return self.payment_received()

        if status == PaymentStatus.FAILED:
            return self.payment_failed()

        if status == PaymentStatus.REFUNDED:
            return self.refund_processed()

        return self.request_payment()