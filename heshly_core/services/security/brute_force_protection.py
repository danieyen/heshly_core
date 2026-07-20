from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


# =====================================================
# Failed Attempt
# =====================================================

@dataclass(slots=True)
class FailedAttempt:

    username: str

    ip_address: str

    attempts: int = 0

    first_attempt: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_attempt: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    locked_until: datetime | None = None


# =====================================================
# Brute Force Protection
# =====================================================

class BruteForceProtection:
    """
    Protects authentication endpoints from
    repeated failed login attempts.
    """

    def __init__(

        self,

        max_attempts: int = 5,

        lockout_minutes: int = 15,

        window_minutes: int = 15,

    ):

        self.max_attempts = max_attempts

        self.lockout_minutes = lockout_minutes

        self.window = timedelta(
            minutes=window_minutes
        )

        self._attempts: dict[
            tuple[str, str],
            FailedAttempt,
        ] = {}

    # =====================================================
    # Internal
    # =====================================================

    def _key(
        self,
        username: str,
        ip_address: str,
    ):

        return (
            username,
            ip_address,
        )

    # =====================================================
    # Failed Login
    # =====================================================

    def record_failure(

        self,

        username: str,

        ip_address: str,

    ) -> FailedAttempt:

        key = self._key(
            username,
            ip_address,
        )

        now = datetime.now(UTC)

        attempt = self._attempts.get(
            key
        )

        if attempt is None:

            attempt = FailedAttempt(

                username=username,

                ip_address=ip_address,

            )

            self._attempts[key] = attempt

        if (
            now - attempt.last_attempt
        ) > self.window:

            attempt.attempts = 0

            attempt.first_attempt = now

        attempt.attempts += 1

        attempt.last_attempt = now

        if (
            attempt.attempts
            >=
            self.max_attempts
        ):

            attempt.locked_until = (

                now
                +
                timedelta(
                    minutes=self.lockout_minutes
                )

            )

        return attempt

    # =====================================================
    # Successful Login
    # =====================================================

    def record_success(

        self,

        username: str,

        ip_address: str,

    ):

        key = self._key(
            username,
            ip_address,
        )

        self._attempts.pop(
            key,
            None,
        )

    # =====================================================
    # Status
    # =====================================================

    def is_blocked(

        self,

        username: str,

        ip_address: str,

    ) -> bool:

        attempt = self._attempts.get(

            self._key(
                username,
                ip_address,
            )

        )

        if attempt is None:

            return False

        if attempt.locked_until is None:

            return False

        if datetime.now(UTC) >= attempt.locked_until:

            attempt.locked_until = None

            attempt.attempts = 0

            return False

        return True

    def remaining_attempts(

        self,

        username: str,

        ip_address: str,

    ) -> int:

        attempt = self._attempts.get(

            self._key(
                username,
                ip_address,
            )

        )

        if attempt is None:

            return self.max_attempts

        remaining = (
            self.max_attempts
            -
            attempt.attempts
        )

        return max(
            remaining,
            0,
        )

    # =====================================================
    # Management
    # =====================================================

    def unlock(

        self,

        username: str,

        ip_address: str,

    ):

        self.record_success(
            username,
            ip_address,
        )

    def clear(self):

        self._attempts.clear()

    def count(self):

        return len(
            self._attempts
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "brute_force_protection",

            "tracked_accounts": self.count(),

            "status": "healthy",

        }