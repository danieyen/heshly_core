from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.quote import (
    Quote,
    QuoteStatus,
)


class QuoteApproval:
    """
    Quote Approval Engine.

    Responsible for:

    - Approval workflow
    - Rejection workflow
    - Submission for approval
    - Approval thresholds
    - Status validation
    - Approval history
    """

    def __init__(
        self,
        auto_approve_limit: float = 10000.0,
    ):

        self.auto_approve_limit = auto_approve_limit

        self._history: list[dict] = []

    # =====================================================
    # Submission
    # =====================================================

    def submit(
        self,
        quote: Quote,
    ) -> Quote:

        if quote.status != QuoteStatus.DRAFT:

            raise ValueError(
                "Only draft quotes can be submitted."
            )

        if quote.grand_total <= self.auto_approve_limit:

            quote.status = QuoteStatus.SENT

            self._record(
                quote,
                "Auto Approved",
                "System",
            )

        else:

            self._record(
                quote,
                "Submitted",
                "System",
            )

        quote.updated_at = datetime.now(UTC)

        return quote

    # =====================================================
    # Approval
    # =====================================================

    def approve(
        self,
        quote: Quote,
        approved_by: str,
    ) -> Quote:

        quote.approved_by = approved_by

        quote.status = QuoteStatus.SENT

        quote.updated_at = datetime.now(UTC)

        self._record(

            quote,

            "Approved",

            approved_by,

        )

        return quote

    # =====================================================
    # Reject
    # =====================================================

    def reject(
        self,
        quote: Quote,
        rejected_by: str,
        reason: str,
    ) -> Quote:

        quote.status = QuoteStatus.REJECTED

        quote.updated_at = datetime.now(UTC)

        self._record(

            quote,

            f"Rejected: {reason}",

            rejected_by,

        )

        return quote

    # =====================================================
    # Cancel
    # =====================================================

    def cancel(
        self,
        quote: Quote,
        cancelled_by: str,
        reason: str = "",
    ) -> Quote:

        quote.status = QuoteStatus.CANCELLED

        quote.updated_at = datetime.now(UTC)

        self._record(

            quote,

            f"Cancelled: {reason}",

            cancelled_by,

        )

        return quote

    # =====================================================
    # Customer Response
    # =====================================================

    def accept(
        self,
        quote: Quote,
    ) -> Quote:

        quote.status = QuoteStatus.ACCEPTED

        quote.updated_at = datetime.now(UTC)

        self._record(

            quote,

            "Customer Accepted",

            "Customer",

        )

        return quote

    def expire(
        self,
        quote: Quote,
    ) -> Quote:

        quote.status = QuoteStatus.EXPIRED

        quote.updated_at = datetime.now(UTC)

        self._record(

            quote,

            "Expired",

            "System",

        )

        return quote

    # =====================================================
    # Rules
    # =====================================================

    def requires_approval(
        self,
        quote: Quote,
    ) -> bool:

        return (

            quote.grand_total

            > self.auto_approve_limit

        )

    # =====================================================
    # History
    # =====================================================

    def history(
        self,
        quote: Quote,
    ) -> list[dict]:

        return [

            record

            for record in self._history

            if (

                record["quote_id"]

                == quote.quote_id

            )

        ]

    def _record(
        self,
        quote: Quote,
        action: str,
        user: str,
    ) -> None:

        self._history.append(

            {

                "quote_id": quote.quote_id,

                "action": action,

                "user": user,

                "timestamp": datetime.now(UTC),

            }

        )