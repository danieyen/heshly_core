from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.quote import (
    Quote,
    QuoteStatus,
)


class QuoteStatusTracker:
    """
    Tracks quote status changes and maintains
    a complete audit history.

    Supported lifecycle:

        DRAFT
            ↓
        SENT
         ↙   ↘
    ACCEPTED REJECTED
         ↓
      CANCELLED (optional)

    EXPIRED may occur from any non-final state.
    """

    FINAL_STATUSES = {
        QuoteStatus.ACCEPTED,
        QuoteStatus.REJECTED,
        QuoteStatus.CANCELLED,
        QuoteStatus.EXPIRED,
    }

    def __init__(self):

        self._history: dict[str, list[dict]] = {}

    # =====================================================
    # Status Management
    # =====================================================

    def update_status(
        self,
        quote: Quote,
        new_status: QuoteStatus,
        changed_by: str = "System",
        notes: str | None = None,
    ) -> Quote:

        previous = quote.status

        quote.status = new_status
        quote.updated_at = datetime.now(UTC)

        self._record(

            quote_id=quote.quote_id,

            previous_status=previous,

            new_status=new_status,

            changed_by=changed_by,

            notes=notes,

        )

        return quote

    # =====================================================
    # Convenience Methods
    # =====================================================

    def mark_sent(
        self,
        quote: Quote,
        changed_by: str = "System",
    ):

        return self.update_status(

            quote,

            QuoteStatus.SENT,

            changed_by,

        )

    def mark_accepted(
        self,
        quote: Quote,
        changed_by: str = "Customer",
    ):

        return self.update_status(

            quote,

            QuoteStatus.ACCEPTED,

            changed_by,

        )

    def mark_rejected(
        self,
        quote: Quote,
        changed_by: str = "Customer",
        reason: str | None = None,
    ):

        return self.update_status(

            quote,

            QuoteStatus.REJECTED,

            changed_by,

            reason,

        )

    def mark_cancelled(
        self,
        quote: Quote,
        changed_by: str,
        reason: str | None = None,
    ):

        return self.update_status(

            quote,

            QuoteStatus.CANCELLED,

            changed_by,

            reason,

        )

    def mark_expired(
        self,
        quote: Quote,
    ):

        return self.update_status(

            quote,

            QuoteStatus.EXPIRED,

            "System",

        )

    # =====================================================
    # History
    # =====================================================

    def history(
        self,
        quote_id: str,
    ) -> list[dict]:

        return self._history.get(
            quote_id,
            [],
        )

    def latest_status(
        self,
        quote_id: str,
    ) -> QuoteStatus | None:

        history = self.history(
            quote_id
        )

        if not history:

            return None

        return history[-1][
            "new_status"
        ]

    # =====================================================
    # Helpers
    # =====================================================

    def is_final(
        self,
        quote: Quote,
    ) -> bool:

        return (

            quote.status

            in self.FINAL_STATUSES

        )

    def transition_count(
        self,
        quote_id: str,
    ) -> int:

        return len(

            self.history(
                quote_id
            )

        )

    # =====================================================
    # Internal
    # =====================================================

    def _record(
        self,
        quote_id: str,
        previous_status: QuoteStatus,
        new_status: QuoteStatus,
        changed_by: str,
        notes: str | None,
    ) -> None:

        self._history.setdefault(

            quote_id,

            [],

        ).append(

            {

                "timestamp": datetime.now(
                    UTC
                ),

                "previous_status": previous_status,

                "new_status": new_status,

                "changed_by": changed_by,

                "notes": notes,

            }

        )