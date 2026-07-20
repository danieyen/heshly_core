from __future__ import annotations

from datetime import UTC, datetime, timedelta

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)


class TrialManager:
    """
    Trial Manager.

    Manages SaaS subscription trials.

    Future:
        • Trial reminder emails
        • WhatsApp reminders
        • Automatic billing conversion
        • Promotional trial extensions
    """

    DEFAULT_TRIAL_DAYS = 14

    # =====================================================
    # Trial Lifecycle
    # =====================================================

    def start_trial(
        self,
        subscription: Subscription,
        days: int | None = None,
    ) -> Subscription:

        duration = (
            days
            if days is not None
            else self.DEFAULT_TRIAL_DAYS
        )

        subscription.status = (
            SubscriptionStatus.TRIAL
        )

        subscription.start_date = datetime.now(UTC)

        subscription.trial_end = (
            subscription.start_date
            + timedelta(days=duration)
        )

        return subscription

    def convert_to_paid(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.activate()

        subscription.trial_end = None

        return subscription

    def expire_trial(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.expire()

        return subscription

    # =====================================================
    # Status
    # =====================================================

    def is_trial_active(
        self,
        subscription: Subscription,
    ) -> bool:

        if (
            subscription.status
            != SubscriptionStatus.TRIAL
        ):
            return False

        if subscription.trial_end is None:
            return False

        return datetime.now(UTC) <= subscription.trial_end

    def days_remaining(
        self,
        subscription: Subscription,
    ) -> int:

        if subscription.trial_end is None:
            return 0

        remaining = (
            subscription.trial_end
            - datetime.now(UTC)
        ).days

        return max(0, remaining)

    # =====================================================
    # Helpers
    # =====================================================

    def summary(
        self,
        subscription: Subscription,
    ) -> dict:

        return {
            "status": subscription.status.value,
            "trial_active": self.is_trial_active(
                subscription
            ),
            "days_remaining": self.days_remaining(
                subscription
            ),
        }

    def health(self) -> dict:

        return {
            "service": "trial_manager",
            "status": "healthy",
        }