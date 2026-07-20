from __future__ import annotations

from heshly_core.models.usage import (
    UsageMetric,
)

from heshly_core.models.usage_limits import (
    UsageLimit,
)

from heshly_core.services.billing.usage_calculator import (
    UsageCalculator,
)


class UsageLimits:
    """
    Checks tenant usage against limits.
    """

    def __init__(self):

        self.calculator = UsageCalculator()

        self.limits = {}


    # =====================================================
    # Configure Limit
    # =====================================================

    def set_limit(
        self,
        metric: UsageMetric,
        limit: int | None,
    ):

        self.limits[metric] = UsageLimit(

            metric=metric,

            limit=limit,

        )


    # =====================================================
    # Get Limit
    # =====================================================

    def get_limit(
        self,
        metric: UsageMetric,
    ) -> UsageLimit | None:

        return self.limits.get(
            metric
        )


    # =====================================================
    # Current Usage
    # =====================================================

    def current_usage(
        self,
        tenant_id: str,
        metric: UsageMetric,
    ) -> int:

        return self.calculator.calculate_metric(

            tenant_id,

            metric,

        )


    # =====================================================
    # Check Limit
    # =====================================================

    def exceeded(
        self,
        tenant_id: str,
        metric: UsageMetric,
    ) -> bool:

        limit = self.get_limit(
            metric
        )

        if limit is None:

            return False


        if limit.is_unlimited():

            return False


        return (

            self.current_usage(
                tenant_id,
                metric,
            )

            >

            limit.limit

        )


    # =====================================================
    # Remaining
    # =====================================================

    def remaining(
        self,
        tenant_id: str,
        metric: UsageMetric,
    ) -> int | None:

        limit = self.get_limit(
            metric
        )

        if limit is None:

            return None


        if limit.is_unlimited():

            return None


        remaining = (

            limit.limit

            -

            self.current_usage(
                tenant_id,
                metric,
            )

        )


        return max(
            remaining,
            0,
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "usage_limits",

            "status":
                "healthy",

        }