from __future__ import annotations

from datetime import datetime, UTC

from heshly_core.models.rate_limit import (
    RateLimitRule,
)


class APIRateLimits:
    """
    Controls API request frequency.
    """

    def __init__(self):

        self.rules = {}

        self.requests = {}


    # =====================================================
    # Configure Limit
    # =====================================================

    def set_rule(
        self,
        key: str,
        requests: int,
        window_seconds: int = 60,
    ):

        self.rules[key] = RateLimitRule(

            name=key,

            requests=requests,

            window_seconds=window_seconds,

        )


    # =====================================================
    # Check Request
    # =====================================================

    def allow(
        self,
        key: str,
    ) -> bool:

        rule = self.rules.get(
            key
        )


        if rule is None:

            return True


        now = datetime.now(
            UTC
        )


        history = self.requests.get(
            key,
            []
        )


        history = [

            timestamp

            for timestamp in history

            if (

                now - timestamp

            ).total_seconds()

            <

            rule.window_seconds

        ]


        if len(history) >= rule.requests:

            self.requests[key] = history

            return False


        history.append(
            now
        )


        self.requests[key] = history


        return True


    # =====================================================
    # Require Access
    # =====================================================

    def require(
        self,
        key: str,
    ):

        if not self.allow(key):

            raise PermissionError(
                "API rate limit exceeded"
            )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "api_rate_limits",

            "status":
                "healthy",

        }