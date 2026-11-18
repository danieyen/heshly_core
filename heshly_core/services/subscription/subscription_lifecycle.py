from __future__ import annotations

from datetime import UTC, datetime, timedelta

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)


class SubscriptionLifecycle:
    """
    Controls the Heshly SaaS subscription lifecycle.

    Responsibilities:

    - trial expiration
    - subscription renewal dates
    - payment delinquency
    - grace periods
    - suspension
    - termination
    - access checks
    """

    DEFAULT_GRACE_PERIOD_DAYS = 7

    # =====================================================
    # Lifecycle
    # =====================================================

    def activate(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.activate()

        subscription.grace_period_until = None
        subscription.termination_reason = None

        return subscription

    def suspend(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.suspend()

        return subscription

    def cancel(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.cancel()

        return subscription

    def expire(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.expire()

        return subscription

    def terminate(
        self,
        subscription: Subscription,
        reason: str = "Subscription expired",
    ) -> Subscription:

        subscription.terminate(reason)

        return subscription

    # =====================================================
    # Billing State
    # =====================================================

    def mark_past_due(
        self,
        subscription: Subscription,
        grace_period_days: int | None = None,
    ) -> Subscription:

        subscription.status = (
            SubscriptionStatus.PAST_DUE
        )

        days = (
            grace_period_days
            if grace_period_days is not None
            else self.DEFAULT_GRACE_PERIOD_DAYS
        )

        subscription.grace_period_until = (
            datetime.now(UTC)
            + timedelta(days=days)
        )

        return subscription

    def renew(
        self,
        subscription: Subscription,
        renewal_date: datetime,
    ) -> Subscription:

        subscription.status = (
            SubscriptionStatus.ACTIVE
        )

        subscription.renewal_date = renewal_date

        subscription.grace_period_until = None

        subscription.terminated_on = None

        subscription.termination_reason = None

        return subscription

    # =====================================================
    # Automatic Evaluation
    # =====================================================

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    def evaluate(
        self,
        subscription: Subscription,
        now: datetime | None = None,
    ) -> Subscription:

        now = self._normalize_datetime(
            now or datetime.now(UTC)
        )

        if subscription.renewal_date is not None:
            subscription.renewal_date = (
                self._normalize_datetime(
                    subscription.renewal_date
                )
            )

        if subscription.trial_end is not None:
            subscription.trial_end = (
                self._normalize_datetime(
                    subscription.trial_end
                )
            )

        if subscription.grace_period_until is not None:
            subscription.grace_period_until = (
                self._normalize_datetime(
                    subscription.grace_period_until
                )
            )

        # ---------------------------------------------
        # Already permanently terminated
        # ---------------------------------------------

        if subscription.status in (
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        ):
            return subscription

        # ---------------------------------------------
        # Trial expiration
        # ---------------------------------------------

        if (
            subscription.status
            == SubscriptionStatus.TRIAL
        ):

            if (
                subscription.trial_end
                and now >= subscription.trial_end
            ):

                self.terminate(
                    subscription,
                    "Trial expired",
                )

            return subscription

        # ---------------------------------------------
        # Active subscription reaches renewal date
        # ---------------------------------------------

        if (
            subscription.status
            == SubscriptionStatus.ACTIVE
            and subscription.renewal_date
            and now >= subscription.renewal_date
        ):

            self.mark_past_due(
                subscription
            )

            return subscription

        # ---------------------------------------------
        # Grace period expired
        # ---------------------------------------------

        if (
            subscription.status
            == SubscriptionStatus.PAST_DUE
            and subscription.grace_period_until
            and now >= subscription.grace_period_until
        ):

            self.suspend(
                subscription
            )

            return subscription

        return subscription

    # =====================================================
    # Access
    # =====================================================

    def can_access(
        self,
        subscription: Subscription,
    ) -> bool:

        return subscription.is_active

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        subscription: Subscription,
    ) -> dict:

        return {
            "subscription_id":
                subscription.subscription_id,

            "tenant_id":
                subscription.tenant_id,

            "business_id":
                subscription.business_id,

            "plan":
                subscription.plan.name,

            "status":
                subscription.status.value,

            "active":
                subscription.is_active,

            "renewal_date":
                subscription.renewal_date,

            "grace_period_until":
                subscription.grace_period_until,

            "terminated_on":
                subscription.terminated_on,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {
            "service":
                "subscription_lifecycle",

            "status":
                "healthy",
        }